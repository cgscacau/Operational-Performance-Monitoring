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

# --- INICIALIZAÇÃO DO SESSION STATE ---
# <<< MUDANÇA CRÍTICA AQUI
# Isso garante que os valores padrão sejam definidos apenas uma vez, na primeira execução.
if 'df_meta' not in st.session_state:
    st.session_state.df_meta = 0.92
if 'uf_meta' not in st.session_state:
    st.session_state.uf_meta = 0.85
if 'mtbf' not in st.session_state:
    st.session_state.mtbf = 500
if 'mttr' not in st.session_state:
    st.session_state.mttr = 25
if 'pm_downtime_anual' not in st.session_state:
    st.session_state.pm_downtime_anual = 80
if 'capacidade_horaria' not in st.session_state:
    st.session_state.capacidade_horaria = 100

# --- Título ---
st.title("🎯 Simulador de Metas Operacionais")
st.markdown("Preveja se suas metas de DF e UF são atingíveis com base nos parâmetros de confiabilidade e manutenção.")

# --- Barra Lateral de Entradas (Inputs) ---
st.sidebar.header("Parâmetros de Entrada")

# <<< MUDANÇA CRÍTICA AQUI: Adicionamos o parâmetro 'key' para cada widget
# O 'key' vincula o valor do widget diretamente ao st.session_state.
st.sidebar.subheader("1. Metas Operacionais")
st.sidebar.slider(
    "Meta de Disponibilidade Física (DF)", 0.80, 1.0, 
    key='df_meta',  # Vincula este slider à chave 'df_meta'
    format="%.2f%%"
)
st.sidebar.slider(
    "Meta de Fator de Utilização (UF)", 0.50, 1.0, 
    key='uf_meta',  # Vincula este slider à chave 'uf_meta'
    format="%.2f%%"
)

st.sidebar.subheader("2. Confiabilidade do Ativo")
st.sidebar.number_input("MTBF (horas)", min_value=1, key='mtbf')
st.sidebar.number_input("MTTR (horas)", min_value=1, key='mttr')

st.sidebar.subheader("3. Manutenção e Produção")
st.sidebar.number_input("Horas de Downtime para PM (Anual)", min_value=0, key='pm_downtime_anual')
st.sidebar.number_input("Capacidade de Produção (unidades/hora)", min_value=1, key='capacidade_horaria')


# --- Cálculos Principais ---
# <<< MUDANÇA CRÍTICA AQUI: Lemos os valores diretamente do session_state
HORAS_CALENDARIO_ANO = 8760

df_inerente = df_from_mtbf_mttr(st.session_state.mtbf, st.session_state.mttr)
df_operacional = calculate_operational_df(df_inerente, st.session_state.pm_downtime_anual, HORAS_CALENDARIO_ANO)
producao_prevista = calculate_production(st.session_state.capacidade_horaria, df_operacional, st.session_state.uf_meta, HORAS_CALENDARIO_ANO)
mttr_necessario = mttr_for_df(st.session_state.mtbf, st.session_state.df_meta)
mtbf_necessario = mtbf_for_df(st.session_state.mttr, st.session_state.df_meta)


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
    delta_op = df_operacional - st.session_state.df_meta
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

if df_operacional >= st.session_state.df_meta:
    st.success(f"**Parabéns!** A meta de DF de **{st.session_state.df_meta:.2%}** é **atingível** com os parâmetros atuais, resultando em uma DF operacional de **{df_operacional:.2%}**.")
else:
    st.warning(f"**Atenção!** A meta de DF de **{st.session_state.df_meta:.2%}** **não é atingível** com os parâmetros atuais. A DF operacional prevista é de apenas **{df_operacional:.2%}**.")

    st.markdown("Para atingir a meta, você precisa de uma das seguintes melhorias:")
    st.info(
        f"1. **Melhorar a Manutenabilidade:** Reduzir o MTTR para **{mttr_necessario:.1f} horas** (mantendo o MTBF atual de {st.session_state.mtbf}h).\n"
        f"2. **Melhorar a Confiabilidade:** Aumentar o MTBF para **{mtbf_necessario:.1f} horas** (mantendo o MTTR atual de {st.session_state.mttr}h)."
    )

