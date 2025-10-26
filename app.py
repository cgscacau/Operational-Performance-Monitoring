# app.py

import streamlit as st

# ==================== CONFIGURAÇÃO ====================
st.set_page_config(
    page_title="Análise de Metas de DF e UF",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Análise de Metas: Disponibilidade Física (DF) e Utilização (UF)")
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
    help="Disponibilidade Física: % do tempo que o equipamento está disponível (não quebrado)"
)

uf_meta = st.sidebar.number_input(
    "Meta de UF (%)",
    min_value=0.0,
    max_value=100.0,
    value=85.0,
    step=0.1,
    help="Fator de Utilização: % do tempo disponível que o equipamento será efetivamente usado"
)

st.sidebar.divider()

# <<< NOVA FUNCIONALIDADE: Modo de Entrada >>>
st.sidebar.subheader("Dados de Confiabilidade")

modo_entrada = st.sidebar.radio(
    "Como você quer informar os dados?",
    options=[
        "Informar MTBF e MTTR",
        "Calcular MTTR (tenho DF atual e MTBF)",
        "Calcular MTBF (tenho DF atual e MTTR)"
    ],
    help="Escolha o modo de entrada baseado nos dados que você possui"
)

# Variáveis que serão calculadas
mtbf = None
mttr = None
df_atual_informada = None

if modo_entrada == "Informar MTBF e MTTR":
    # Modo tradicional
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

elif modo_entrada == "Calcular MTTR (tenho DF atual e MTBF)":
    # Calcular MTTR a partir de DF e MTBF
    df_atual_informada = st.sidebar.number_input(
        "DF Atual/Real (%)",
        min_value=0.1,
        max_value=99.9,
        value=90.0,
        step=0.1,
        help="Disponibilidade Física atual do equipamento (sem considerar PM)"
    )
    
    mtbf = st.sidebar.number_input(
        "MTBF (horas)",
        min_value=1,
        value=500,
        help="Tempo Médio Entre Falhas"
    )
    
    # Calcular MTTR
    df_atual_decimal = df_atual_informada / 100
    mttr = (mtbf * (1 - df_atual_decimal)) / df_atual_decimal
    
    st.sidebar.success(f"✅ **MTTR Calculado:** {mttr:.1f} horas")

elif modo_entrada == "Calcular MTBF (tenho DF atual e MTTR)":
    # Calcular MTBF a partir de DF e MTTR
    df_atual_informada = st.sidebar.number_input(
        "DF Atual/Real (%)",
        min_value=0.1,
        max_value=99.9,
        value=90.0,
        step=0.1,
        help="Disponibilidade Física atual do equipamento (sem considerar PM)"
    )
    
    mttr = st.sidebar.number_input(
        "MTTR (horas)",
        min_value=1,
        value=25,
        help="Tempo Médio Para Reparo"
    )
    
    # Calcular MTBF
    df_atual_decimal = df_atual_informada / 100
    mtbf = (mttr * df_atual_decimal) / (1 - df_atual_decimal)
    
    st.sidebar.success(f"✅ **MTBF Calculado:** {mtbf:.1f} horas")

st.sidebar.divider()

st.sidebar.subheader("Manutenção Preventiva")
horas_pm_mes = st.sidebar.number_input(
    "Horas de PM Planejadas no Mês",
    min_value=0,
    value=16,
    help="Total de horas de paradas planejadas para manutenção preventiva"
)

# ==================== CÁLCULOS ====================

# Converter percentuais para decimais
df_meta_decimal = df_meta / 100
uf_meta_decimal = uf_meta / 100

# Horas no mês (considerando 30 dias × 24 horas)
HORAS_CALENDARIO = 30 * 24  # 720 horas

# ===== CÁLCULO DE DF =====
# 1. Downtime por falhas corretivas esperadas
falhas_esperadas_mes = HORAS_CALENDARIO / mtbf
downtime_corretivo = falhas_esperadas_mes * mttr

# 2. Downtime total (corretivo + preventivo)
downtime_total = downtime_corretivo + horas_pm_mes

# 3. Horas Disponíveis e DF Projetada
horas_disponiveis = HORAS_CALENDARIO - downtime_total
df_projetada = horas_disponiveis / HORAS_CALENDARIO

# 4. DF Inerente (sem PM)
df_inerente = mtbf / (mtbf + mttr)

# ===== CÁLCULO DE UF =====
# Horas de operação necessárias para atingir a meta de UF
horas_operacao_necessarias = uf_meta_decimal * horas_disponiveis

# UF projetada (será igual à meta se houver horas disponíveis suficientes)
uf_projetada = uf_meta_decimal if horas_disponiveis > 0 else 0

# ===== VERIFICAÇÃO DE METAS =====
atinge_df = df_projetada >= df_meta_decimal
atinge_uf = horas_disponiveis >= horas_operacao_necessarias
gap_df = df_projetada - df_meta_decimal

# ==================== EXIBIÇÃO DOS RESULTADOS ====================

st.header("📊 Resultados da Análise")

# Mostrar informação sobre o modo de cálculo usado
if modo_entrada != "Informar MTBF e MTTR":
    st.info(f"ℹ️ **Modo de Cálculo:** {modo_entrada}")

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "DF Inerente",
        f"{df_inerente:.1%}",
        help="DF teórica sem considerar PM (baseada em MTBF e MTTR)"
    )

with col2:
    st.metric(
        "DF Projetada",
        f"{df_projetada:.1%}",
        delta=f"{gap_df:.1%} vs Meta",
        delta_color="normal" if atinge_df else "inverse",
        help="Disponibilidade Física esperada (incluindo PM)"
    )

with col3:
    st.metric(
        "Meta de DF",
        f"{df_meta_decimal:.1%}",
        help="Objetivo de Disponibilidade Física"
    )

with col4:
    st.metric(
        "Meta de UF",
        f"{uf_meta_decimal:.1%}",
        help="Objetivo de Utilização"
    )

st.divider()

# Métricas de Confiabilidade
st.subheader("🔧 Parâmetros de Confiabilidade")

col_conf1, col_conf2, col_conf3 = st.columns(3)

with col_conf1:
    st.metric(
        "MTBF",
        f"{mtbf:.1f}h",
        help="Tempo Médio Entre Falhas"
    )

with col_conf2:
    st.metric(
        "MTTR",
        f"{mttr:.1f}h",
        help="Tempo Médio Para Reparo"
    )

with col_conf3:
    st.metric(
        "Horas de Operação Necessárias",
        f"{horas_operacao_necessarias:.0f}h",
        help="Para atingir a meta de UF"
    )

st.divider()

# Análise detalhada
st.subheader("🔍 Análise Detalhada")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### ⏱️ Breakdown de Horas no Mês")
    
    with st.container(border=True):
        st.markdown(f"**Horas no Calendário:** {HORAS_CALENDARIO}h")
        st.markdown(f"**Falhas Esperadas:** {falhas_esperadas_mes:.2f}")
        st.markdown(f"**Downtime Corretivo:** {downtime_corretivo:.1f}h")
        st.markdown(f"**Downtime Preventivo:** {horas_pm_mes:.1f}h")
        st.markdown(f"**Downtime Total:** {downtime_total:.1f}h")
        st.markdown(f"---")
        st.markdown(f"**✅ Horas Disponíveis:** {horas_disponiveis:.1f}h")
        st.markdown(f"**🎯 Horas de Operação Necessárias (UF={uf_meta:.1f}%):** {horas_operacao_necessarias:.1f}h")
        st.markdown(f"**⏸️ Horas Disponíveis Ociosas:** {horas_disponiveis - horas_operacao_necessarias:.1f}h")

with col_b:
    st.markdown("### 📋 Status das Metas")
    
    # Status DF
    if atinge_df:
        st.success(
            f"✅ **META DE DF ATINGÍVEL**\n\n"
            f"DF Projetada: **{df_projetada:.1%}**\n\n"
            f"Meta: **{df_meta_decimal:.1%}**\n\n"
            f"Margem: **+{gap_df:.1%}**"
        )
    else:
        st.error(
            f"❌ **META DE DF NÃO ATINGÍVEL**\n\n"
            f"DF Projetada: **{df_projetada:.1%}**\n\n"
            f"Meta: **{df_meta_decimal:.1%}**\n\n"
            f"Gap: **{gap_df:.1%}**"
        )
    
    st.markdown("---")
    
    # Status UF
    if atinge_uf:
        st.success(
            f"✅ **META DE UF VIÁVEL**\n\n"
            f"Horas disponíveis: **{horas_disponiveis:.1f}h**\n\n"
            f"Horas necessárias para UF={uf_meta:.1f}%: **{horas_operacao_necessarias:.1f}h**\n\n"
            f"Há capacidade suficiente para atingir a meta de utilização."
        )
    else:
        st.error(
            f"❌ **META DE UF INVIÁVEL**\n\n"
            f"Horas disponíveis: **{horas_disponiveis:.1f}h**\n\n"
            f"Horas necessárias para UF={uf_meta:.1f}%: **{horas_operacao_necessarias:.1f}h**\n\n"
            f"⚠️ **Problema:** Não há horas disponíveis suficientes."
        )
        
        uf_maxima = (horas_disponiveis / horas_operacao_necessarias) * uf_meta_decimal if horas_operacao_necessarias > 0 else 0
        st.info(f"💡 Com a DF projetada de {df_projetada:.1%}, o UF máximo atingível seria **{uf_maxima:.1%}**")

st.divider()

# Recomendações
if not atinge_df:
    st.subheader("💡 Recomendações para Atingir a Meta de DF")
    
    # Calcular downtime máximo permitido
    downtime_maximo = HORAS_CALENDARIO * (1 - df_meta_decimal)
    reducao_necessaria = downtime_total - downtime_maximo
    
    st.info(f"Para atingir {df_meta:.1f}% de DF, o downtime total não pode exceder **{downtime_maximo:.1f}h**. "
            f"Atualmente está projetado em **{downtime_total:.1f}h**. "
            f"Necessário reduzir em **{reducao_necessaria:.1f}h**.")
    
    col_rec1, col_rec2, col_rec3 = st.columns(3)
    
    with col_rec1:
        # Opção 1: Reduzir MTTR
        mttr_necessario = (downtime_maximo - horas_pm_mes) / falhas_esperadas_mes
        if mttr_necessario > 0:
            reducao_mttr = mttr - mttr_necessario
            st.markdown(f"""
            **Opção 1: Melhorar Manutenabilidade**
            - Reduzir MTTR de **{mttr:.1f}h** para **{mttr_necessario:.1f}h**
            - Redução: **{reducao_mttr:.1f}h** ({reducao_mttr/mttr*100:.1f}%)
            """)
    
    with col_rec2:
        # Opção 2: Aumentar MTBF
        mtbf_necessario = HORAS_CALENDARIO / ((downtime_maximo - horas_pm_mes) / mttr)
        aumento_mtbf = mtbf_necessario - mtbf
        st.markdown(f"""
        **Opção 2: Melhorar Confiabilidade**
        - Aumentar MTBF de **{mtbf:.1f}h** para **{mtbf_necessario:.1f}h**
        - Aumento: **{aumento_mtbf:.1f}h** ({aumento_mtbf/mtbf*100:.1f}%)
        """)
    
    with col_rec3:
        # Opção 3: Reduzir PM
        pm_maximo = downtime_maximo - downtime_corretivo
        if pm_maximo > 0:
            reducao_pm = horas_pm_mes - pm_maximo
            st.markdown(f"""
            **Opção 3: Otimizar PM**
            - Reduzir PM de **{horas_pm_mes:.1f}h** para **{pm_maximo:.1f}h**
            - Redução: **{reducao_pm:.1f}h** ({reducao_pm/horas_pm_mes*100:.1f}%)
            """)

elif not atinge_uf:
    st.subheader("💡 Recomendações para Viabilizar a Meta de UF")
    
    st.warning(
        f"A meta de UF de **{uf_meta:.1f}%** requer **{horas_operacao_necessarias:.1f}h** de operação, "
        f"mas apenas **{horas_disponiveis:.1f}h** estarão disponíveis."
    )
    
    st.markdown("**Opções:**")
    st.markdown(f"1. **Melhorar a DF** para ter mais horas disponíveis")
    st.markdown(f"2. **Revisar a meta de UF** para um valor mais realista (máximo atingível: {(horas_disponiveis/horas_operacao_necessarias)*uf_meta:.1f}%)")

# Informações adicionais
with st.expander("ℹ️ Definições e Fórmulas"):
    st.markdown("""
    ### Disponibilidade Física (DF)
    Percentual do tempo em que o equipamento está **fisicamente disponível** para operar.

    
    $$DF = \\frac{\\text{Horas Calendário} - \\text{Downtime Total}}{\\text{Horas Calendário}}$$
    
    ### DF Inerente (sem PM)

    $$DF_{inerente} = \\frac{MTBF}{MTBF + MTTR}$$
    
    ### Cálculos Reversos
    
    **Se você tem DF e MTBF, pode calcular MTTR:**

    $$MTTR = \\frac{MTBF \\times (1 - DF)}{DF}$$
    
    **Se você tem DF e MTTR, pode calcular MTBF:**

    $$MTBF = \\frac{MTTR \\times DF}{1 - DF}$$
    
    ### Fator de Utilização (UF)

    $$UF = \\frac{\\text{Horas Operadas}}{\\text{Horas Disponíveis}}$$
    
    ### MTBF e MTTR
    - **MTBF:** Tempo médio entre falhas (maior = melhor)
    - **MTTR:** Tempo médio para reparo (menor = melhor)
    """)
