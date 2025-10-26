# app.py

import streamlit as st
from datetime import datetime
from core import (
    df_from_mtbf_mttr,
    calculate_operational_df,
    calculate_production,
    mttr_for_df,
    mtbf_for_df
)

# --- Configuração da Página ---
st.set_page_config(
    page_title="Simulador e Monitor de Metas",
    page_icon="🎯",
    layout="wide"
)

# --- INICIALIZAÇÃO DO SESSION STATE ---
if 'df_meta' not in st.session_state:
    st.session_state.df_meta = 0.8020  # Meta de 80,20%
if 'uf_meta' not in st.session_state:
    st.session_state.uf_meta = 0.85
if 'mtbf' not in st.session_state:
    st.session_state.mtbf = 500
if 'mttr' not in st.session_state:
    st.session_state.mttr = 25
if 'pm_downtime_mensal' not in st.session_state:
    st.session_state.pm_downtime_mensal = 8
# <<< MUDANÇA AQUI: Novos estados para dados realizados >>>
# Valores padrão para replicar o seu exemplo de 80,0% no dia e 79,9% no mês 26
if 'downtime_dia_atual' not in st.session_state:
    st.session_state.downtime_dia_atual = 4.8 # (1 - 0.80) * 24 horas
if 'downtime_mes_acumulado' not in st.session_state:
    st.session_state.downtime_mes_acumulado = 125.42 # (1 - 0.799) * 26 dias * 24 horas

# --- Título ---
st.title("🎯 Simulador e Monitor de Metas Operacionais")
st.markdown("Use a barra lateral para simular cenários e monitorar o desempenho real.")

# --- Barra Lateral de Entradas (Inputs) ---
st.sidebar.header("Parâmetros de Entrada")

# --- Seção de Simulação ---
st.sidebar.subheader("Simulação de Cenários")
st.sidebar.slider(
    "Meta de Disponibilidade Física (DF)", 0.80, 1.0, 
    key='df_meta',
    format="%.2f%%"
)
st.sidebar.slider("Meta de Fator de Utilização (UF)", 0.50, 1.0, key='uf_meta', format="%.2f%%")
st.sidebar.number_input("MTBF (horas)", min_value=1, key='mtbf')
st.sidebar.number_input("MTTR (horas)", min_value=1, key='mttr')
st.sidebar.number_input("Horas de Downtime para PM (Mensal)", min_value=0, key='pm_downtime_mensal')

# <<< MUDANÇA AQUI: Nova seção para dados realizados >>>
st.sidebar.divider()
st.sidebar.subheader("Monitoramento do Realizado")
data_atual = datetime(2025, 10, 26) # Usando a data do seu exemplo
st.sidebar.info(f"Dados para: **{data_atual.strftime('%d/%m/%Y')}**")

st.sidebar.number_input(
    f"Horas de Downtime Hoje (dia {data_atual.day})", 
    min_value=0.0,
    key='downtime_dia_atual',
    format="%.2f"
)
st.sidebar.number_input(
    f"Downtime Acumulado no Mês (até hoje)", 
    min_value=0.0,
    key='downtime_mes_acumulado',
    format="%.2f"
)
st.sidebar.divider()

# --- Painel Principal ---
col_simulador, col_monitor = st.columns(2)

# --- COLUNA 1: SIMULADOR (o que já tínhamos) ---
with col_simulador:
    st.header("Análise Preditiva (Simulador)")
    
    # Cálculos da Simulação
    HORAS_CALENDARIO_ANO = 8760
    pm_downtime_anual_calculado = st.session_state.pm_downtime_mensal * 12
    df_inerente = df_from_mtbf_mttr(st.session_state.mtbf, st.session_state.mttr)
    df_operacional = calculate_operational_df(df_inerente, pm_downtime_anual_calculado, HORAS_CALENDARIO_ANO)
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric(
            label="DF Inerente (Teórica)",
            value=f"{df_inerente:.2%}".replace('.', ','),
        )
    with c2:
        delta_op = df_operacional - st.session_state.df_meta
        st.metric(
            label="DF Operacional (Prevista)",
            value=f"{df_operacional:.2%}".replace('.', ','),
            delta=f"{delta_op:.2%}".replace('.', ','),
            delta_color="normal" if delta_op >= 0 else "inverse",
        )
    
    st.subheader("Análise de Viabilidade da Meta")
    if df_operacional >= st.session_state.df_meta:
        st.success(f"**Atingível:** A DF prevista de **{df_operacional:.2%}** supera a meta de **{st.session_state.df_meta:.2%}**.".replace('.', ','))
    else:
        mttr_nec = mttr_for_df(st.session_state.mtbf, st.session_state.df_meta)
        mtbf_nec = mtbf_for_df(st.session_state.mttr, st.session_state.df_meta)
        st.warning(f"**Não Atingível:** A DF prevista é de apenas **{df_operacional:.2%}**.".replace('.', ','))
        st.info(f"Para atingir a meta, seria necessário um MTTR de **{mttr_nec:.1f}h** ou um MTBF de **{mtbf_nec:.1f}h**.".replace('.', ','))

# <<< MUDANÇA AQUI: Nova coluna para o monitoramento >>>
# --- COLUNA 2: MONITORAMENTO ---
with col_monitor:
    st.header("Acompanhamento do Realizado")
    
    # Cálculos do Realizado
    DIA_DO_MES = data_atual.day
    HORAS_NO_DIA = 24.0
    
    # DF do Dia
    horas_operadas_dia = HORAS_NO_DIA - st.session_state.downtime_dia_atual
    df_exec_dia = horas_operadas_dia / HORAS_NO_DIA if HORAS_NO_DIA > 0 else 0

    # DF do Mês
    horas_totais_mes = DIA_DO_MES * HORAS_NO_DIA
    horas_operadas_mes = horas_totais_mes - st.session_state.downtime_mes_acumulado
    df_exec_mes = horas_operadas_mes / horas_totais_mes if horas_totais_mes > 0 else 0

    # Determinar status
    status_dia = "🟢" if df_exec_dia >= st.session_state.df_meta else "🔴"
    status_mes = "🟢" if df_exec_mes >= st.session_state.df_meta else "🔴"
    
    # Exibição no formato da sua imagem
    with st.container(border=True):
        st.subheader("Transporte")
        st.markdown(f"**DF Orçado:** `{st.session_state.df_meta:.2%}`".replace('.', ','))
        st.markdown(f"### {status_dia} DF Exec Dia: `{df_exec_dia:.1%}`".replace('.', ','))
        st.markdown(f"### {status_mes} DF Exec Mês: `{df_exec_mes:.1%}`".replace('.', ','))
