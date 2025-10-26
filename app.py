# app.py

import streamlit as st
from core import (
    df_from_mtbf_mttr,
    calculate_operational_df,
    calculate_production,
    mttr_for_df,
    mtbf_for_df
)

# --- Configuração da Página ---
st.set_page_config(
    page_title="Simulador de Metas Operacionais",
    page_icon="🎯",
    layout="wide"
)

# --- Título ---
st.title("🎯 Simulador de Metas Operacionais")
st.markdown("Preveja se suas metas de DF e UF são atingíveis com base nos parâmetros de confiabilidade e manutenção.")

# --- Barra Lateral de Entradas (Inputs) ---
st.sidebar.header("Parâmetros de Entrada")

# Metas Operacionais
st.sidebar.subheader("1. Metas Operacionais")
df_meta = st.sidebar.slider("Meta de Disponibilidade Física (DF)", 0.80, 1.0, 0.92, 0.01, format="%.2f%%")
uf_meta = st.sidebar.slider("Meta de Fator de Utilização (UF)", 0.50, 1.0, 0.85, 0.01, format="%.2f%%")

# Confiabilidade
st.sidebar.subheader("2. Confiabilidade do Ativo")
mtbf = st.sidebar.number_input("MTBF (horas)", min_value=1, value=500)
mttr = st.sidebar.number_input("MTTR (horas)", min_value=1, value=25)

# Manutenção e Produção
st.sidebar.subheader("3. Manutenção e Produção")
pm_downtime_anual = st.sidebar.number_input("Horas de Downtime para PM (Anual)", min_value=0, value=80)
capacidade_horaria = st.sidebar.number_input("Capacidade de Produção (unidades/hora)", min_value=1, value=100)

# --- Cálculos Principais ---
HORAS_CALENDARIO_ANO = 8760

# Disponibilidade Inerente (Teórica)
df_inerente = df_from_mtbf_mttr(mtbf, mttr)

# Disponibilidade Operacional
df_operacional = calculate_operational_df(df_inerente, pm_downtime_anual, HORAS_CALENDARIO_ANO)

# Produção Prevista
producao_prevista = calculate_production(capacidade_horaria, df_operacional, uf_meta, HORAS_CALENDARIO_ANO)

# Análise "What-If" para atingir a meta
mttr_necessario = mttr_for_df(mtbf, df_meta)
mtbf_necessario = mtbf_for_df(mttr, df_meta)


# --- Dashboard Principal (Resultados) ---
st.header("Resultados Determinísticos")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Disponibilidade Inerente (Teórica)",
        value=f"{df_inerente:.2%}",
        help="DF máxima possível, considerando apenas falhas e reparos (MTBF / (MTBF + MTTR))."
    )

with col2:
    delta_op = df_operacional - df_meta
    st.metric(
        label="Disponibilidade Operacional Prevista",
        value=f"{df_operacional:.2%}",
        delta=f"{delta_op:.2%} vs Meta",
        delta_color="normal" if delta_op >= 0 else "inverse",
        help="DF realista, descontando as paradas planejadas para manutenção preventiva."
    )

with col3:
    st.metric(
        label="Produção Anual Prevista",
        value=f"{producao_prevista:,.0f} unidades",
        help="Produção total estimada com base na DF Operacional e no Fator de Utilização."
    )

st.markdown("---")
st.subheader("Análise de Viabilidade da Meta")

if df_operacional >= df_meta:
    st.success(f"**Parabéns!** A meta de DF de **{df_meta:.2%}** é **atingível** com os parâmetros atuais, resultando em uma DF operacional de **{df_operacional:.2%}**.")
else:
    st.warning(f"**Atenção!** A meta de DF de **{df_meta:.2%}** **não é atingível** com os parâmetros atuais. A DF operacional prevista é de apenas **{df_operacional:.2%}**.")

    st.markdown("Para atingir a meta, você precisa de uma das seguintes melhorias:")
    st.info(
        f"1. **Melhorar a Manutenabilidade:** Reduzir o MTTR para **{mttr_necessario:.1f} horas** (mantendo o MTBF atual de {mtbf}h).\n"
        f"2. **Melhorar a Confiabilidade:** Aumentar o MTBF para **{mtbf_necessario:.1f} horas** (mantendo o MTTR atual de {mttr}h)."
    )


