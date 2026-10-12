"""
Módulo de conexão com o banco de dados PostgreSQL via SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env caso exista
load_dotenv()

# Parâmetros de conexão com valores padrão para o contêiner Docker
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "iot_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def get_engine() -> Engine:
    """
    Retorna a instância do SQLAlchemy Engine configurada.
    """
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def test_connection() -> bool:
    """
    Testa se a conexão com o banco de dados está ativa.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.exec_driver_sql("SELECT 1;")
            return result.scalar() == 1
    except Exception as exc:
        print(f"Erro ao conectar com o banco de dados: {exc}")
        return False


if __name__ == "__main__":
    if test_connection():
        print(f" Conexão estabelecida com sucesso no banco: {DB_NAME} ({DB_HOST}:{DB_PORT})")
    else:
        print(" Falha ao conectar ao banco de dados.")
