# app.py

import streamlit as st
from datetime import datetime
from core import (
    df_from_mtbf_mttr,
    calculate_operational_df,
    mttr_for_df,
    mtbf_for_df,
    formatar_percentual
)

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Simulador de Metas",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== INICIALIZAÇÃO DO SESSION STATE ====================
# <<< MUDANÇA AQUI: Valores agora são percentuais (0-100) >>>
if 'df_meta' not in st.session_state:
    st.session_state.df_meta = 92.0  # 92%
if 'uf_meta' not in st.session_state:
    st.session_state.uf_meta = 85.0  # 85%
if 'mtbf' not in st.session_state:
    st.session_state.mtbf = 500
if 'mttr' not in st.session_state:
    st.session_state.mttr = 25
if 'pm_downtime_mensal' not in st.session_state:
    st.session_state.pm_downtime_mensal = 8

# ==================== CABEÇALHO ====================
st.title("🎯 Simulador de Metas Operacionais")
st.markdown("Analise a viabilidade das suas metas de Disponibilidade Física (DF) e Fator de Utilização (UF).")

# ==================== BARRA LATERAL - INPUTS ====================
with st.sidebar:
    st.header("⚙️ Parâmetros de Simulação")
    
    st.subheader("Metas Operacionais")
    st.slider(
        "Meta de DF (%)",
        min_value=80.0,
        max_value=100.0,
        key='df_meta',
        format="%.1f%%",
        help="Disponibilidade Física alvo"
    )
    st.slider(
        "Meta de UF (%)",
        min_value=50.0,
        max_value=100.0,
        key='uf_meta',
        format="%.1f%%",
        help="Fator de Utilização alvo"
    )
    
    st.divider()
    st.subheader("Confiabilidade do Ativo")
    st.number_input(
        "MTBF (horas)",
        min_value=1,
        key='mtbf',
        help="Tempo Médio Entre Falhas"
    )
    st.number_input(
        "MTTR (horas)",
        min_value=1,
        key='mttr',
        help="Tempo Médio Para Reparo"
    )
    
    st.divider()
    st.subheader("Manutenção Preventiva")
    st.number_input(
        "Downtime PM Mensal (horas)",
        min_value=0,
        key='pm_downtime_mensal',
        help="Horas de parada para manutenção preventiva por mês"
    )

# ==================== CÁLCULOS PRINCIPAIS ====================
# <<< MUDANÇA AQUI: Converter percentuais para decimais para os cálculos >>>
df_meta_decimal = st.session_state.df_meta / 100.0
uf_meta_decimal = st.session_state.uf_meta / 100.0

# Constantes
HORAS_ANO = 8760
pm_downtime_anual = st.session_state.pm_downtime_mensal * 12

# Cálculos
df_inerente = df_from_mtbf_mttr(st.session_state.mtbf, st.session_state.mttr)
df_operacional = calculate_operational_df(df_inerente, pm_downtime_anual, HORAS_ANO)
mttr_necessario = mttr_for_df(st.session_state.mtbf, df_meta_decimal)
mtbf_necessario = mtbf_for_df(st.session_state.mttr, df_meta_decimal)

# ==================== DASHBOARD PRINCIPAL ====================
st.header("📊 Resultados da Simulação")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="DF Inerente",
        value=formatar_percentual(df_inerente),
        help="Disponibilidade teórica máxima (MTBF / (MTBF + MTTR))"
    )

with col2:
    delta = df_operacional - df_meta_decimal
    st.metric(
        label="DF Operacional",
        value=formatar_percentual(df_operacional),
        delta=formatar_percentual(delta),
        delta_color="normal" if delta >= 0 else "inverse",
        help="DF realista, considerando paradas para PM"
    )

with col3:
    st.metric(
        label="Meta de DF",
        value=formatar_percentual(df_meta_decimal),
        help="Seu objetivo de Disponibilidade Física"
    )

# ==================== ANÁLISE DE VIABILIDADE ====================
st.divider()
st.subheader("🔍 Análise de Viabilidade")

if df_operacional >= df_meta_decimal:
    st.success(
        f"✅ **Meta Atingível!** A DF operacional projetada de **{formatar_percentual(df_operacional)}** "
        f"supera a meta de **{formatar_percentual(df_meta_decimal)}**."
    )
else:
    st.warning(
        f"⚠️ **Meta Não Atingível.** A DF operacional projetada é de apenas **{formatar_percentual(df_operacional)}**, "
        f"abaixo da meta de **{formatar_percentual(df_meta_decimal)}**."
    )
    
    st.markdown("### 💡 Ações Necessárias")
    st.markdown(
        f"Para atingir a meta de **{formatar_percentual(df_meta_decimal)}**, você precisa de **uma** das seguintes melhorias:"
    )
    
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("**Opção 1: Melhorar Manutenabilidade**")
            st.metric(
                "MTTR Necessário",
                f"{mttr_necessario:.1f}h",
                delta=f"{mttr_necessario - st.session_state.mttr:.1f}h",
                delta_color="inverse"
            )
            st.caption(f"(mantendo MTBF = {st.session_state.mtbf}h)")
    
    with col_b:
        with st.container(border=True):
            st.markdown("**Opção 2: Melhorar Confiabilidade**")
            st.metric(
                "MTBF Necessário",
                f"{mtbf_necessario:.1f}h",
                delta=f"{mtbf_necessario - st.session_state.mtbf:.1f}h",
                delta_color="normal"
            )
            st.caption(f"(mantendo MTTR = {st.session_state.mttr}h)")
