"""
Pipeline ETL: Extração, Transformação e Carga das leituras de IoT no PostgreSQL.
"""

import os
import sys
import time
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text
from src.database import get_engine, test_connection


def find_csv_file() -> Path:
    """
    Localiza o arquivo CSV no diretório data/ ou na raiz do projeto.
    """
    possible_paths = [
        Path("data/IOT-temp.csv"),
        Path("IOT-temp.csv"),
        Path(__file__).resolve().parent.parent / "data" / "IOT-temp.csv",
        Path(__file__).resolve().parent.parent / "IOT-temp.csv",
    ]
    for path in possible_paths:
        if path.exists():
            return path.resolve()
    raise FileNotFoundError("Arquivo IOT-temp.csv não foi encontrado nem em data/ nem na raiz.")


def extract_data(csv_path: Path) -> pd.DataFrame:
    """
    Lê o dataset bruto a partir do arquivo CSV.
    """
    print(f"[*] Extraindo dados de: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"    - Registros lidos: {len(df):,} linhas e {len(df.columns)} colunas.")
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica as transformações e higienizações necessárias nos dados:
    - Deduplicação de IDs;
    - Padronização de nomes de colunas;
    - Conversão e parsing de datas;
    - Mapeamento do identificador de dispositivo (device_id);
    - Tipagem correta dos dados numéricos.
    """
    print("[*] Iniciando etapa de transformação e limpeza...")
    
    # 1. Deduplicação por id
    initial_count = len(df)
    df = df.drop_duplicates(subset=["id"], keep="first").copy()
    duplicates_removed = initial_count - len(df)
    if duplicates_removed > 0:
        print(f"    - Registros duplicados removidos: {duplicates_removed}")

    # 2. Renomeação de colunas para snake_case compatível com PostgreSQL
    column_mapping = {
        "id": "id",
        "room_id/id": "room_id",
        "noted_date": "noted_date",
        "temp": "temperature",
        "out/in": "out_in",
    }
    df = df.rename(columns=column_mapping)

    # 3. Conversão de datas (formato brasileiro DD-MM-YYYY HH:MM)
    df["noted_date"] = pd.to_datetime(df["noted_date"], format="%d-%m-%Y %H:%M")

    # 4. Criação do device_id enriquecido (ex.: 'Room Admin (In)' e 'Room Admin (Out)')
    df["device_id"] = df["room_id"] + " (" + df["out_in"] + ")"

    # 5. Garantia de tipagem
    df["temperature"] = df["temperature"].astype(float)
    df["room_id"] = df["room_id"].astype(str)
    df["out_in"] = df["out_in"].astype(str)
    df["device_id"] = df["device_id"].astype(str)

    # 6. Reordenação das colunas conforme schema do banco
    final_columns = ["id", "room_id", "out_in", "device_id", "temperature", "noted_date"]
    df = df[final_columns]

    print(f"    - Registros válidos após transformação: {len(df):,}")
    print(f"    - Período monitorado: {df['noted_date'].min()} até {df['noted_date'].max()}")
    print(f"    - Dispositivos mapeados: {list(df['device_id'].unique())}")
    return df


def load_data(df: pd.DataFrame, chunksize: int = 10000) -> None:
    """
    Insere os dados tratados no PostgreSQL em lotes eficientes.
    """
    print("[*] Iniciando carga no PostgreSQL...")
    engine = get_engine()

    with engine.begin() as connection:
        # Garante idempotência limpando registros anteriores
        print("    - Limpando registros antigos da tabela temperature_readings (TRUNCATE CASCADE)...")
        connection.execute(text("TRUNCATE TABLE temperature_readings CASCADE;"))

    start_time = time.time()
    total_rows = len(df)
    inserted = 0

    print(f"    - Inserindo {total_rows:,} registros com tamanho de lote = {chunksize:,}...")
    for i in range(0, total_rows, chunksize):
        chunk = df.iloc[i:i + chunksize]
        chunk.to_sql(
            name="temperature_readings",
            con=engine,
            if_exists="append",
            index=False,
            method="multi",
        )
        inserted += len(chunk)
        print(f"      Progresso: {inserted:,}/{total_rows:,} registros inseridos ({inserted / total_rows * 100:.1f}%)")

    elapsed_time = time.time() - start_time
    print(f"[+] Carga finalizada com sucesso em {elapsed_time:.2f} segundos!")


def validate_pipeline() -> None:
    """
    Verifica se a tabela e as 3 Views SQL estão povoadas e respondendo corretamente.
    """
    print("\n[*] Validando integridade e consultas analíticas no banco:")
    engine = get_engine()
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM temperature_readings;")).scalar()
        print(f"    Total na tabela 'temperature_readings': {total:,} registros")

        print("\n--- VIEW 1: avg_temp_por_dispositivo ---")
        df_v1 = pd.read_sql("SELECT * FROM avg_temp_por_dispositivo;", conn)
        print(df_v1.to_string(index=False))

        print("\n--- VIEW 2: leituras_por_hora (amostra das primeiras 6 horas) ---")
        df_v2 = pd.read_sql("SELECT * FROM leituras_por_hora LIMIT 6;", conn)
        print(df_v2.to_string(index=False))

        print("\n--- VIEW 3: temp_max_min_por_dia (amostra dos primeiros 5 dias) ---")
        df_v3 = pd.read_sql("SELECT * FROM temp_max_min_por_dia ORDER BY data ASC LIMIT 5;", conn)
        print(df_v3.to_string(index=False))


def run_pipeline() -> None:
    """
    Executa o ciclo completo de ETL.
    """
    print("==================================================")
    print("      INICIANDO PIPELINE DE DADOS IOT (ETL)       ")
    print("==================================================")

    if not test_connection():
        print("[!] Erro: Não foi possível conectar ao PostgreSQL. Verifique se o contêiner Docker está ativo.")
        sys.exit(1)

    csv_path = find_csv_file()
    df_raw = extract_data(csv_path)
    df_transformed = transform_data(df_raw)
    load_data(df_transformed, chunksize=10000)
    validate_pipeline()

    print("\n==================================================")
    print("      PIPELINE DE DADOS CONCLUÍDO COM SUCESSO!     ")
    print("==================================================")


if __name__ == "__main__":
    run_pipeline()
