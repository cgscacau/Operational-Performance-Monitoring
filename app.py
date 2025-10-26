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
    help="Fator de Utilização: % do tempo disponível que o equipamento foi efetivamente usado"
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

st.sidebar.subheader("Manutenção Preventiva")
horas_pm_mes = st.sidebar.number_input(
    "Horas de PM Planejadas no Mês",
    min_value=0,
    value=16,
    help="Total de horas de paradas planejadas para manutenção preventiva"
)

st.sidebar.divider()

st.sidebar.subheader("Utilização Esperada")
horas_operacao_planejadas = st.sidebar.number_input(
    "Horas de Operação Planejadas no Mês",
    min_value=0,
    value=600,
    help="Quantas horas você planeja usar o equipamento (demanda operacional)"
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

# 3. DF Projetada
horas_disponiveis = HORAS_CALENDARIO - downtime_total
df_projetada = horas_disponiveis / HORAS_CALENDARIO

# ===== CÁLCULO DE UF =====
# UF = Horas Operadas / Horas Disponíveis
# Limitado pelas horas disponíveis (não pode operar mais do que está disponível)
horas_operadas_possiveis = min(horas_operacao_planejadas, horas_disponiveis)
uf_projetada = horas_operadas_possiveis / horas_disponiveis if horas_disponiveis > 0 else 0

# ===== VERIFICAÇÃO DE METAS =====
atinge_df = df_projetada >= df_meta_decimal
atinge_uf = uf_projetada >= uf_meta_decimal
gap_df = df_projetada - df_meta_decimal
gap_uf = uf_projetada - uf_meta_decimal

# ==================== EXIBIÇÃO DOS RESULTADOS ====================

st.header(f"📊 Análise: {nome_equipamento}")

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "DF Projetada",
        f"{df_projetada:.1%}",
        delta=f"{gap_df:.1%} vs Meta",
        delta_color="normal" if atinge_df else "inverse",
        help="Disponibilidade Física esperada"
    )

with col2:
    st.metric(
        "Meta de DF",
        f"{df_meta_decimal:.1%}",
        help="Objetivo de Disponibilidade Física"
    )

with col3:
    st.metric(
        "UF Projetada",
        f"{uf_projetada:.1%}",
        delta=f"{gap_uf:.1%} vs Meta",
        delta_color="normal" if atinge_uf else "inverse",
        help="Fator de Utilização esperado"
    )

with col4:
    st.metric(
        "Meta de UF",
        f"{uf_meta_decimal:.1%}",
        help="Objetivo de Utilização"
    )

st.divider()

# Análise detalhada
st.subheader("🔍 Análise Detalhada")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### ⏱️ Breakdown de Horas no Mês")
    
    with st.container(border=True):
        st.markdown(f"**Horas no Calendário:** {HORAS_CALENDARIO}h")
        st.markdown(f"**Downtime Corretivo:** {downtime_corretivo:.1f}h ({falhas_esperadas_mes:.2f} falhas esperadas)")
        st.markdown(f"**Downtime Preventivo:** {horas_pm_mes:.1f}h")
        st.markdown(f"**Downtime Total:** {downtime_total:.1f}h")
        st.markdown(f"---")
        st.markdown(f"**✅ Horas Disponíveis:** {horas_disponiveis:.1f}h")
        st.markdown(f"**🔧 Horas Operadas (planejadas):** {horas_operadas_possiveis:.1f}h")
        st.markdown(f"**⏸️ Horas Disponíveis não Utilizadas:** {horas_disponiveis - horas_operadas_possiveis:.1f}h")

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
            f"✅ **META DE UF ATINGÍVEL**\n\n"
            f"UF Projetada: **{uf_projetada:.1%}**\n\n"
            f"Meta: **{uf_meta_decimal:.1%}**\n\n"
            f"Margem: **+{gap_uf:.1%}**"
        )
    else:
        st.warning(
            f"⚠️ **META DE UF NÃO ATINGÍVEL**\n\n"
            f"UF Projetada: **{uf_projetada:.1%}**\n\n"
            f"Meta: **{uf_meta_decimal:.1%}**\n\n"
            f"Gap: **{gap_uf:.1%}**"
        )
        
        if horas_operacao_planejadas > horas_disponiveis:
            st.info(
                f"💡 **Atenção:** Você planejou operar {horas_operacao_planejadas}h, "
                f"mas o equipamento só estará disponível por {horas_disponiveis:.1f}h. "
                f"O UF está limitado pela disponibilidade."
            )

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
    
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        # Opção 1: Reduzir MTTR
        mttr_necessario = (downtime_maximo - horas_pm_mes) / falhas_esperadas_mes
        if mttr_necessario > 0:
            reducao_mttr = mttr - mttr_necessario
            st.markdown(f"""
            **Opção 1: Melhorar Manutenabilidade**
            - Reduzir MTTR de **{mttr}h** para **{mttr_necessario:.1f}h**
            - Redução necessária: **{reducao_mttr:.1f}h** ({reducao_mttr/mttr*100:.1f}%)
            """)
    
    with col_rec2:
        # Opção 2: Aumentar MTBF
        mtbf_necessario = HORAS_CALENDARIO / ((downtime_maximo - horas_pm_mes) / mttr)
        aumento_mtbf = mtbf_necessario - mtbf
        st.markdown(f"""
        **Opção 2: Melhorar Confiabilidade**
        - Aumentar MTBF de **{mtbf}h** para **{mtbf_necessario:.1f}h**
        - Aumento necessário: **{aumento_mtbf:.1f}h** ({aumento_mtbf/mtbf*100:.1f}%)
        """)

# Informações adicionais
with st.expander("ℹ️ Definições e Conceitos"):
    st.markdown("""
    ### Disponibilidade Física (DF)
    Percentual do tempo em que o equipamento está **fisicamente disponível** para operar (não quebrado, não em manutenção).

    
    $$DF = \\frac{\\text{Horas Calendário} - \\text{Downtime Total}}{\\text{Horas Calendário}}$$
    
    ### Fator de Utilização (UF)
    Do tempo que o equipamento está disponível, quanto foi **efetivamente utilizado** (demanda operacional).

    
    $$UF = \\frac{\\text{Horas Operadas}}{\\text{Horas Disponíveis}}$$
    
    ### MTBF (Mean Time Between Failures)
    Tempo médio entre falhas. Quanto **maior**, melhor a confiabilidade.
    
    ### MTTR (Mean Time To Repair)
    Tempo médio para reparo. Quanto **menor**, melhor a manutenabilidade.
    
    ### Relação entre DF e UF
    - **DF** depende da confiabilidade e manutenção do equipamento
    - **UF** depende da demanda operacional e da DF
    - Um equipamento pode ter alta DF mas baixa UF (disponível mas não usado)
    - Um equipamento não pode ter alta UF se tiver baixa DF (não pode usar o que não está disponível)
    """)
