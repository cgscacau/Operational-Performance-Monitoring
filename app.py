# app.py

import streamlit as st
import numpy as np

# ==================== CONFIGURAÇÃO ====================
st.set_page_config(
    page_title="Análise de Metas de DF",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Análise de Probabilidade de Atingimento de Metas")
st.markdown("Verifique se seus equipamentos atingirão as metas de DF e UF do mês.")

# ==================== ENTRADAS ====================
st.sidebar.header("📋 Configuração")

st.sidebar.subheader("Metas do Mês")
df_meta = st.sidebar.number_input(
    "Meta de DF (%)",
    min_value=0.0,
    max_value=100.0,
    value=92.0,
    step=0.1,
    help="Disponibilidade Física alvo para o mês"
)

uf_meta = st.sidebar.number_input(
    "Meta de UF (%)",
    min_value=0.0,
    max_value=100.0,
    value=85.0,
    step=0.1,
    help="Fator de Utilização alvo para o mês"
)

st.sidebar.divider()

st.sidebar.subheader("Dados do Equipamento")
nome_equipamento = st.sidebar.text_input(
    "Nome/ID do Equipamento",
    value="CAM-001",
    help="Identificação do equipamento"
)

mtbf = st.sidebar.number_input(
    "MTBF (horas)",
    min_value=1,
    value=500,
    help="Tempo Médio Entre Falhas"
)

mttr = st.sidebar.number_input(
    "MTTR (horas)",
    min_value=1,
    value=25,
    help="Tempo Médio Para Reparo"
)

st.sidebar.divider()

st.sidebar.subheader("Parâmetros do Mês")
horas_pm_mes = st.sidebar.number_input(
    "Horas de PM Planejadas no Mês",
    min_value=0,
    value=16,
    help="Total de horas de manutenção preventiva planejadas"
)

# ==================== CÁLCULOS ====================

# Converter percentuais para decimais
df_meta_decimal = df_meta / 100
uf_meta_decimal = uf_meta / 100

# Horas no mês (considerando 30 dias)
HORAS_MES = 30 * 24  # 720 horas

# 1. Calcular DF Inerente (teórica, sem PM)
df_inerente = mtbf / (mtbf + mttr)

# 2. Calcular DF Operacional (considerando PM)
impacto_pm = horas_pm_mes / HORAS_MES
df_operacional = df_inerente - impacto_pm

# 3. Calcular downtime esperado por falhas no mês
falhas_esperadas_mes = HORAS_MES / mtbf
downtime_corretivo_esperado = falhas_esperadas_mes * mttr

# 4. Calcular DF projetada real
downtime_total_mes = downtime_corretivo_esperado + horas_pm_mes
df_projetada = 1 - (downtime_total_mes / HORAS_MES)

# 5. Verificar se atinge a meta
atinge_df = df_projetada >= df_meta_decimal
gap_df = df_projetada - df_meta_decimal

# ==================== EXIBIÇÃO DOS RESULTADOS ====================

st.header(f"📊 Análise: {nome_equipamento}")

# Métricas principais
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "DF Inerente",
        f"{df_inerente:.1%}",
        help="Disponibilidade teórica sem considerar PM"
    )

with col2:
    cor_delta = "normal" if atinge_df else "inverse"
    st.metric(
        "DF Projetada",
        f"{df_projetada:.1%}",
        delta=f"{gap_df:.1%} vs Meta",
        delta_color=cor_delta,
        help="Disponibilidade real esperada para o mês"
    )

with col3:
    st.metric(
        "Meta de DF",
        f"{df_meta_decimal:.1%}",
        help="Objetivo estabelecido"
    )

st.divider()

# Análise detalhada
st.subheader("🔍 Análise Detalhada")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### Breakdown de Horas no Mês")
    st.markdown(f"**Total de horas no mês:** {HORAS_MES}h")
    st.markdown(f"**Falhas esperadas:** {falhas_esperadas_mes:.2f}")
    st.markdown(f"**Downtime por falhas:** {downtime_corretivo_esperado:.1f}h")
    st.markdown(f"**Downtime por PM:** {horas_pm_mes:.1f}h")
    st.markdown(f"**Downtime total:** {downtime_total_mes:.1f}h")
    st.markdown(f"**Horas operacionais:** {HORAS_MES - downtime_total_mes:.1f}h")

with col_b:
    st.markdown("### Conclusão")
    if atinge_df:
        st.success(
            f"✅ **META ATINGÍVEL**\n\n"
            f"O equipamento **{nome_equipamento}** deve atingir a meta de DF de **{df_meta:.1f}%**.\n\n"
            f"DF Projetada: **{df_projetada:.1%}**\n\n"
            f"Margem de segurança: **{gap_df:.1%}**"
        )
    else:
        st.error(
            f"❌ **META NÃO ATINGÍVEL**\n\n"
            f"O equipamento **{nome_equipamento}** não deve atingir a meta de DF de **{df_meta:.1f}%**.\n\n"
            f"DF Projetada: **{df_projetada:.1%}**\n\n"
            f"Gap: **{gap_df:.1%}**"
        )
        
        # Calcular o que seria necessário
        st.markdown("### 💡 O que seria necessário?")
        
        # Opção 1: Reduzir MTTR
        mttr_necessario = (mtbf * (1 - df_meta_decimal)) / df_meta_decimal - (horas_pm_mes * mtbf / HORAS_MES)
        if mttr_necessario > 0:
            reducao_mttr = mttr - mttr_necessario
            st.info(f"**Opção 1:** Reduzir o MTTR em **{reducao_mttr:.1f}h** (de {mttr}h para {mttr_necessario:.1f}h)")
        
        # Opção 2: Aumentar MTBF
        mtbf_necessario = (mttr + horas_pm_mes * HORAS_MES / HORAS_MES) * df_meta_decimal / (1 - df_meta_decimal)
        aumento_mtbf = mtbf_necessario - mtbf
        st.info(f"**Opção 2:** Aumentar o MTBF em **{aumento_mtbf:.1f}h** (de {mtbf}h para {mtbf_necessario:.1f}h)")

st.divider()

# Informações adicionais
with st.expander("ℹ️ Como interpretar os resultados"):
    st.markdown("""
    **DF (Disponibilidade Física):** Percentual do tempo em que o equipamento está disponível para operar.
    
    **DF Inerente:** Considera apenas falhas aleatórias (MTBF e MTTR). É o "potencial" do equipamento.
    
    **DF Projetada:** Considera falhas aleatórias + paradas planejadas para manutenção preventiva. É a realidade esperada.
    
    **MTBF (Mean Time Between Failures):** Tempo médio entre falhas. Quanto maior, melhor.
    
    **MTTR (Mean Time To Repair):** Tempo médio para reparo. Quanto menor, melhor.
    
    **Como melhorar a DF:**
    - Aumentar o MTBF (melhorar confiabilidade através de melhorias, treinamento de operadores, etc.)
    - Reduzir o MTTR (melhorar manutenabilidade através de peças de reposição, treinamento de mecânicos, etc.)
    - Otimizar o plano de PM (reduzir horas de parada preventiva sem comprometer a confiabilidade)
    """)
