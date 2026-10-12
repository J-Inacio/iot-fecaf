"""
Dashboard Interativo de Monitoramento de Temperaturas IoT.
Construído com Streamlit, Plotly e PostgreSQL via SQLAlchemy.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text

# Garante que o diretório raiz esteja no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import get_engine, DB_NAME, DB_HOST, DB_PORT

# Configuração da página Streamlit
st.set_page_config(
    page_title="Dashboard de Temperaturas IoT | UniFECAF",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização complementar em CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #9E9E9E;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background-color: #1E222D;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Conexão com o banco de dados via engine centralizada
engine = get_engine()


@st.cache_data(ttl=60)
def load_data(view_name: str) -> pd.DataFrame:
    """
    Carrega os dados de uma view do PostgreSQL em um DataFrame do Pandas.
    """
    return pd.read_sql(f"SELECT * FROM {view_name}", engine)


@st.cache_data(ttl=60)
def load_kpis() -> dict:
    """
    Obtém indicadores globais do banco de dados para os cards de destaque.
    """
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT 
                COUNT(*) AS total_leituras,
                ROUND(AVG(temperature), 2) AS temp_media,
                MAX(temperature) AS temp_max,
                MIN(temperature) AS temp_min,
                MIN(noted_date)::DATE AS data_inicio,
                MAX(noted_date)::DATE AS data_fim
            FROM temperature_readings;
        """)).mappings().first()
        return dict(res) if res else {}


# ==========================================
# Barra Lateral (Sidebar)
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/thermometer.png", width=72)
    st.title("Painel IoT")
    st.markdown("**Disruptive Architectures**")
    st.caption("IoT, Big Data & PostgreSQL")
    
    st.divider()
    st.markdown("### 🔌 Status da Infraestrutura")
    st.success(f"Banco: `{DB_NAME}`\n\nHost: `{DB_HOST}:{DB_PORT}`\n\nDocker: Ativo")

    st.divider()
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("📌 **Entregáveis:**")
    st.markdown("- Pipeline de Ingestão Python")
    st.markdown("- Banco de Dados PostgreSQL Docker")
    st.markdown("- 3 Views SQL Analíticas")
    st.markdown("- Visualização com Plotly")


# ==========================================
# Cabeçalho Principal
# ==========================================
st.markdown('<div class="main-title">🌡️ Dashboard de Temperaturas IoT</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Monitoramento e análise preditiva de séries temporais de sensores de temperatura IoT</div>', unsafe_allow_html=True)

# Cards de Métricas Principais (KPIs)
kpis = load_kpis()
if kpis:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="📊 Total de Leituras", value=f"{kpis.get('total_leituras', 0):,}")
    with col2:
        st.metric(label="🌡️ Temp. Média Geral", value=f"{kpis.get('temp_media', 0):.2f} °C")
    with col3:
        st.metric(label="🔥 Temp. Máxima", value=f"{kpis.get('temp_max', 0)} °C")
    with col4:
        st.metric(label="❄️ Temp. Mínima", value=f"{kpis.get('temp_min', 0)} °C")
    with col5:
        st.metric(label="📅 Período Coletado", value=f"{kpis.get('data_inicio')} a {kpis.get('data_fim')}")

st.divider()

# ==========================================
# Gráfico 1: Média de Temperatura por Dispositivo
# ==========================================
st.header("1. Média de Temperatura por Dispositivo")
st.caption("Comparação térmica média entre os dispositivos instalados em ambientes internos e externos.")

df_avg_temp = load_data("avg_temp_por_dispositivo")

col_g1, col_t1 = st.columns([2.5, 1])
with col_g1:
    fig1 = px.bar(
        df_avg_temp,
        x="device_id",
        y="avg_temp",
        color="device_id",
        text="avg_temp",
        labels={"device_id": "Dispositivo / Ambiente", "avg_temp": "Temperatura Média (°C)"},
        color_discrete_sequence=["#00b4d8", "#f77f00"],
        title="Média de Temperatura (°C) por Dispositivo"
    )
    fig1.update_traces(texttemplate='%{text:.2f} °C', textposition='outside')
    fig1.update_layout(showlegend=False, yaxis_range=[0, max(df_avg_temp['avg_temp']) * 1.25])
    st.plotly_chart(fig1, use_container_width=True)

with col_t1:
    st.markdown("#### Tabela de Dados")
    st.dataframe(df_avg_temp, hide_index=True, use_container_width=True)
    st.info("💡 **Insight:** O sensor externo ('Out') apresenta média de ~36.27 °C, consideravelmente superior ao sensor interno ('In') de ~30.45 °C, demonstrando isolamento térmico na sala administrativa.")

st.divider()

# ==========================================
# Gráfico 2: Contagem de Leituras por Hora
# ==========================================
st.header("2. Leituras por Hora do Dia")
st.caption("Distribuição da frequência de telemetria transmitida pelos sensores nas 24 horas.")

df_leituras_hora = load_data("leituras_por_hora")

fig2 = px.line(
    df_leituras_hora,
    x="hora",
    y="contagem",
    markers=True,
    labels={"hora": "Hora do Dia (0h - 23h)", "contagem": "Total de Leituras Recebidas"},
    title="Volume de Leituras de Sensores IoT por Hora",
    color_discrete_sequence=["#06d6a0"]
)
fig2.update_xaxes(tickmode="linear", tick0=0, dtick=1)
fig2.update_layout(hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)

with st.expander("🔍 Ver dados detalhados por hora do dia"):
    st.dataframe(df_leituras_hora, hide_index=True, use_container_width=True)

st.divider()

# ==========================================
# Gráfico 3: Temperaturas Máximas e Mínimas por Dia
# ==========================================
st.header("3. Temperaturas Máximas e Mínimas por Dia")
st.caption("Variação da amplitude térmica histórica registrada ao longo de todo o período monitorado.")

df_temp_max_min = load_data("temp_max_min_por_dia")

fig3 = px.line(
    df_temp_max_min,
    x="data",
    y=["temp_max", "temp_min"],
    labels={"data": "Data da Leitura", "value": "Temperatura (°C)", "variable": "Métrica"},
    title="Evolução Temporal: Temperaturas Máximas e Mínimas Diárias",
    color_discrete_map={"temp_max": "#ef476f", "temp_min": "#118ab2"}
)
fig3.update_layout(
    legend_title_text="Legenda",
    hovermode="x unified"
)
st.plotly_chart(fig3, use_container_width=True)

with st.expander("🔍 Ver histórico diário completo de máximas e mínimas"):
    st.dataframe(df_temp_max_min, hide_index=True, use_container_width=True)

# Rodapé
st.markdown("---")
st.caption("Desenvolvido para a disciplina Disruptive Architectures: IoT, Big Data e IA — UniFECAF.")
