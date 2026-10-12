# 🌡️ Pipeline de Dados IoT com Docker, PostgreSQL e Streamlit

Projeto desenvolvido para a disciplina **Disruptive Architectures: IoT, Big Data e IA** na **UniFECAF**.

Este projeto implementa um pipeline de dados completo de ponta a ponta (ETL), processando medições reais de sensores de temperatura IoT, armazenando os dados estruturados em um banco relacional PostgreSQL conteinerizado com Docker e disponibilizando um painel analítico interativo via Streamlit e Plotly.

---

## 🚀 Tecnologias Utilizadas

- **Linguagem:** [Python 3.12](https://www.python.org/)
- **Manipulação de Dados:** [Pandas](https://pandas.pydata.org/)
- **ORM / Conectividade:** [SQLAlchemy](https://www.sqlalchemy.org/) & [Psycopg2](https://www.psycopg.org/)
- **Banco de Dados:** [PostgreSQL 16](https://www.postgresql.org/)
- **Conteinerização:** [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- **Visualização / Dashboard:** [Streamlit](https://streamlit.io/) & [Plotly Express](https://plotly.com/python/)
- **Controle de Versão:** [Git](https://git-scm.com/) & [GitHub](https://github.com/)

---

## 📁 Estrutura do Projeto

```text
iot-fecaf/
├── data/
│   └── IOT-temp.csv               # Dataset com ~97 mil leituras de sensores
├── sql/
│   ├── init.sql                   # DDL da tabela temperature_readings e índices
│   └── views.sql                  # DDL das 3 Views SQL analíticas requeridas
├── src/
│   ├── __init__.py                # Inicializador do pacote Python
│   ├── database.py                # Conexão e engine SQLAlchemy
│   ├── etl.py                     # Pipeline de ingestão, limpeza e carga
│   └── dashboard.py               # Interface gráfica e visualização com Streamlit
├── docker-compose.yml             # Orquestração do contêiner PostgreSQL
├── requirements.txt               # Dependências do projeto
├── .gitignore                     # Arquivos ignorados pelo Git
└── README.md                      # Documentação completa do projeto
```

---

## 🛠️ Pré-requisitos

- **Docker** e **Docker Compose** instalados e em execução.
- **Python 3.10+** (com suporte a criação de ambientes virtuais `venv`).
- **Git** instalado para clonagem e versionamento.

---

## ⚙️ Passo a Passo para Configuração e Execução

### 1. Clonar o Repositório e Acessar o Diretório

```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd iot-fecaf
```

### 2. Configurar o Ambiente Virtual Python

Crie e ative o ambiente virtual isolado:

```bash
# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente virtual (Linux/macOS)
source .venv/bin/activate

# Ativar no Windows (Prompt / PowerShell)
# .venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### 3. Subir o Banco de Dados PostgreSQL no Docker

Você pode iniciar o PostgreSQL via **Docker Compose**:

```bash
docker-compose up -d
```

*Ou diretamente via comando `docker run`:*

```bash
docker run --name postgres-iot \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=iot_db \
  -p 5432:5432 \
  -d postgres:16-alpine
```

Para verificar se o contêiner está saudável e aceitando conexões:

```bash
docker exec postgres-iot pg_isready -U postgres -d iot_db
```

### 4. Executar o Pipeline de Ingestão e Carga (ETL)

O script `src/etl.py` executa o fluxo completo:
1. Carrega os dados brutos de `data/IOT-temp.csv`.
2. Remove registros duplicados.
3. Padroniza colunas, converte tipos e faz o parsing de datas (`DD-MM-YYYY HH:MM`).
4. Cria o identificador de dispositivo `device_id` combinando sala e localização (`In`/`Out`).
5. Realiza a carga em lotes (*batch insert*) no PostgreSQL e valida as 3 Views SQL.

Execute:

```bash
python src/etl.py
```

### 5. Iniciar o Dashboard Interativo

Com os dados populados no PostgreSQL, inicialize o dashboard Streamlit:

```bash
streamlit run src/dashboard.py
```

Acesse em seu navegador o endereço indicado (por padrão: [http://localhost:8501](http://localhost:8501)).

---

## 📊 Views SQL e Modelagem Analítica

O projeto cria e consome três visões analíticas (`Views`) otimizadas no PostgreSQL:

### 1. `avg_temp_por_dispositivo`
- **Propósito:** Calcular a temperatura média registrada por cada sensor/dispositivo para avaliar diferenças térmicas entre ambientes internos e externos.
- **Definição SQL:**
```sql
CREATE OR REPLACE VIEW avg_temp_por_dispositivo AS
SELECT 
    device_id, 
    ROUND(AVG(temperature), 2) AS avg_temp
FROM temperature_readings
GROUP BY device_id;
```

### 2. `leituras_por_hora`
- **Propósito:** Agrupar e contabilizar as leituras nas 24 horas do dia para analisar padrões de frequência da telemetria IoT e possíveis oscilações no tráfego de rede.
- **Definição SQL:**
```sql
CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT 
    EXTRACT(HOUR FROM noted_date)::INT AS hora,
    COUNT(*) AS contagem
FROM temperature_readings
GROUP BY hora
ORDER BY hora;
```

### 3. `temp_max_min_por_dia`
- **Propósito:** Identificar a amplitude térmica diária (temperatura máxima e mínima) ao longo de todo o período monitorado, permitindo detectar anomalias climáticas.
- **Definição SQL:**
```sql
CREATE OR REPLACE VIEW temp_max_min_por_dia AS
SELECT 
    DATE(noted_date) AS data,
    MAX(temperature) AS temp_max,
    MIN(temperature) AS temp_min
FROM temperature_readings
GROUP BY DATE(noted_date)
ORDER BY data;
```

---

## 💡 Principais Insights Obtidos

1. **Diferença Térmica Interno vs. Externo:**
   - O sensor externo (`Room Admin (Out)`) registrou temperatura média de **36.27 °C**, enquanto o sensor interno (`Room Admin (In)`) registrou média de **30.45 °C**. Isso demonstra eficácia no isolamento do ambiente interno ou atuação de refrigeração controlada.
2. **Distribuição das Leituras por Hora:**
   - O volume de telemetria é contínuo 24 horas por dia, com picos de leituras no início da manhã (por volta das 05h), sugerindo um ciclo programado de sincronização ou aquecimento de rotina dos dispositivos.
3. **Amplitude Térmica e Estabilidade:**
   - Há consistência na variação térmica entre os dias com mínimas na faixa de 25°C–31°C e máximas atingindo picos superiores a 40°C no sensor externo nos períodos mais quentes.

