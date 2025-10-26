# app.py

import streamlit as st

# ==================== CONFIGURAÇÃO ====================
st.set_page_config(
    page_title="Calculadora de Disponibilidade",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Calculadora de Disponibilidade Física (DF)")
st.markdown("Relacione DF, MTBF, MTTR e Manutenção Preventiva.")

# ==================== SELEÇÃO DO MODO DE CÁLCULO ====================
st.sidebar.header("⚙️ Modo de Cálculo")

modo = st.sidebar.radio(
    "O que você deseja calcular?",
    [
        "Calcular DF (tenho MTBF e MTTR)",
        "Calcular MTBF (tenho DF e MTTR)",
        "Calcular MTTR (tenho DF e MTBF)"
    ]
)

st.sidebar.divider()

# ==================== CONFIGURAÇÃO DO PERÍODO ====================
st.sidebar.subheader("⏱️ Período de Análise")

periodo = st.sidebar.selectbox(
    "Período",
    ["Mensal (30 dias)", "Anual (365 dias)", "Personalizado"],
    help="Período para análise da disponibilidade"
)

if periodo == "Mensal (30 dias)":
    horas_periodo = 30 * 24
elif periodo == "Anual (365 dias)":
    horas_periodo = 365 * 24
else:
    dias_personalizados = st.sidebar.number_input(
        "Número de dias",
        min_value=1,
        value=30,
        step=1
    )
    horas_periodo = dias_personalizados * 24

st.sidebar.info(f"📅 Período: **{horas_periodo}h** ({horas_periodo/24:.0f} dias)")

st.sidebar.divider()

# ==================== ENTRADAS BASEADAS NO MODO ====================

if modo == "Calcular DF (tenho MTBF e MTTR)":
    st.sidebar.subheader("Dados de Confiabilidade")
    
    mtbf = st.sidebar.number_input(
        "MTBF (horas)",
        min_value=0.1,
        value=500.0,
        step=10.0,
        help="Tempo Médio Entre Falhas"
    )
    
    mttr = st.sidebar.number_input(
        "MTTR (horas)",
        min_value=0.1,
        value=25.0,
        step=1.0,
        help="Tempo Médio Para Reparo"
    )
    
    st.sidebar.divider()
    st.sidebar.subheader("Manutenção Preventiva")
    
    horas_pm = st.sidebar.number_input(
        f"Horas de PM no período ({horas_periodo/24:.0f} dias)",
        min_value=0.0,
        value=16.0,
        step=1.0,
        help="Total de horas de parada para manutenção preventiva no período"
    )
    
    # Cálculos
    df_inerente = mtbf / (mtbf + mttr)
    impacto_pm = horas_pm / horas_periodo
    df_operacional = df_inerente - impacto_pm
    
    # Garantir que não seja negativo
    df_operacional = max(0, df_operacional)
    
    # Cálculo de downtime
    falhas_esperadas = horas_periodo / mtbf
    downtime_corretivo = falhas_esperadas * mttr
    downtime_total = downtime_corretivo + horas_pm
    
    # Exibição
    st.header("📊 Resultados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("MTBF", f"{mtbf:.1f}h", help="Tempo Médio Entre Falhas")
    
    with col2:
        st.metric("MTTR", f"{mttr:.1f}h", help="Tempo Médio Para Reparo")
    
    with col3:
        st.metric("DF Inerente", f"{df_inerente:.2%}", help="Disponibilidade sem considerar PM")
    
    with col4:
        delta_df = df_operacional - df_inerente
        st.metric(
            "DF Operacional", 
            f"{df_operacional:.2%}", 
            delta=f"{delta_df:.2%}",
            delta_color="inverse",
            help="Disponibilidade real considerando PM"
        )
    
    st.divider()
    
    # Breakdown detalhado
    st.subheader("🔍 Análise Detalhada do Período")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        with st.container(border=True):
            st.markdown("### ⏱️ Breakdown de Horas")
            st.markdown(f"**Horas totais no período:** {horas_periodo:.0f}h")
            st.markdown(f"**Falhas esperadas:** {falhas_esperadas:.2f}")
            st.markdown(f"**Downtime por falhas:** {downtime_corretivo:.1f}h")
            st.markdown(f"**Downtime por PM:** {horas_pm:.1f}h")
            st.markdown(f"**Downtime total:** {downtime_total:.1f}h")
            st.markdown(f"---")
            st.markdown(f"**✅ Horas disponíveis:** {horas_periodo - downtime_total:.1f}h")
    
    with col_b:
        with st.container(border=True):
            st.markdown("### 📊 Impacto da PM")
            st.markdown(f"**DF Inerente (sem PM):** {df_inerente:.2%}")
            st.markdown(f"**Impacto da PM:** -{impacto_pm:.2%}")
            st.markdown(f"**DF Operacional (com PM):** {df_operacional:.2%}")
            st.markdown(f"---")
            perda_percentual = (impacto_pm / df_inerente * 100) if df_inerente > 0 else 0
            st.markdown(f"**Perda relativa:** {perda_percentual:.1f}% da DF inerente")
    
    st.divider()
    
    # Explicação dos cálculos
    with st.container(border=True):
        st.markdown("### 📐 Cálculos Realizados")
        
        st.markdown("**1. DF Inerente (baseada em confiabilidade):**")
        st.latex(r"DF_{inerente} = \frac{MTBF}{MTBF + MTTR}")
        st.latex(rf"DF_{inerente} = \frac{{{mtbf}}}{{{mtbf} + {mttr}}} = {df_inerente:.4f} = {df_inerente:.2%}")
        
        st.markdown("**2. Impacto da Manutenção Preventiva:**")
        st.latex(r"Impacto_{PM} = \frac{\text{Horas de PM}}{\text{Horas do Período}}")
        st.latex(rf"Impacto_{PM} = \frac{{{horas_pm}}}{{{horas_periodo}}} = {impacto_pm:.4f} = {impacto_pm:.2%}")
        
        st.markdown("**3. DF Operacional (realidade):**")
        st.latex(r"DF_{operacional} = DF_{inerente} - Impacto_{PM}")
        st.latex(rf"DF_{operacional} = {df_inerente:.4f} - {impacto_pm:.4f} = {df_operacional:.4f} = {df_operacional:.2%}")

elif modo == "Calcular MTBF (tenho DF e MTTR)":
    st.sidebar.subheader("Dados de Entrada")
    
    df_alvo = st.sidebar.number_input(
        "DF Alvo (%)",
        min_value=0.1,
        max_value=99.9,
        value=95.0,
        step=0.1,
        help="Disponibilidade Física desejada"
    ) / 100
    
    mttr = st.sidebar.number_input(
        "MTTR (horas)",
        min_value=0.1,
        value=25.0,
        step=1.0,
        help="Tempo Médio Para Reparo"
    )
    
    st.sidebar.divider()
    st.sidebar.subheader("Manutenção Preventiva")
    
    horas_pm = st.sidebar.number_input(
        f"Horas de PM no período ({horas_periodo/24:.0f} dias)",
        min_value=0.0,
        value=16.0,
        step=1.0,
        help="Total de horas de parada para manutenção preventiva"
    )
    
    # Cálculos
    impacto_pm = horas_pm / horas_periodo
    df_inerente_necessaria = df_alvo + impacto_pm
    
    # Verificar se é possível
    if df_inerente_necessaria >= 1.0:
        st.error("❌ **Impossível atingir esta meta!** Mesmo com MTBF infinito e MTTR zero, a PM sozinha impede atingir esta DF.")
        st.stop()
    
    mtbf = (mttr * df_inerente_necessaria) / (1 - df_inerente_necessaria)
    
    # Exibição
    st.header("📊 Resultado")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("DF Alvo", f"{df_alvo:.2%}")
    
    with col2:
        st.metric("MTTR (entrada)", f"{mttr:.1f}h")
    
    with col3:
        st.metric("MTBF Necessário", f"{mtbf:.1f}h", help="MTBF necessário para atingir a meta")
    
    with col4:
        st.metric("DF Inerente Necessária", f"{df_inerente_necessaria:.2%}", help="Sem considerar PM")
    
    st.divider()
    
    with st.container(border=True):
        st.markdown("### 📐 Cálculo Realizado")
        
        st.markdown(f"**1. Impacto da PM:** {impacto_pm:.2%}")
        st.markdown(f"**2. DF Inerente necessária:** {df_alvo:.2%} + {impacto_pm:.2%} = {df_inerente_necessaria:.2%}")
        
        st.markdown("**3. MTBF necessário:**")
        st.latex(r"MTBF = \frac{MTTR \times DF_{inerente}}{1 - DF_{inerente}}")
        st.latex(rf"MTBF = \frac{{{mttr} \times {df_inerente_necessaria:.4f}}}{{1 - {df_inerente_necessaria:.4f}}} = {mtbf:.1f}h")

elif modo == "Calcular MTTR (tenho DF e MTBF)":
    st.sidebar.subheader("Dados de Entrada")
    
    df_alvo = st.sidebar.number_input(
        "DF Alvo (%)",
        min_value=0.1,
        max_value=99.9,
        value=95.0,
        step=0.1,
        help="Disponibilidade Física desejada"
    ) / 100
    
    mtbf = st.sidebar.number_input(
        "MTBF (horas)",
        min_value=0.1,
        value=500.0,
        step=10.0,
        help="Tempo Médio Entre Falhas"
    )
    
    st.sidebar.divider()
    st.sidebar.subheader("Manutenção Preventiva")
    
    horas_pm = st.sidebar.number_input(
        f"Horas de PM no período ({horas_periodo/24:.0f} dias)",
        min_value=0.0,
        value=16.0,
        step=1.0,
        help="Total de horas de parada para manutenção preventiva"
    )
    
    # Cálculos
    impacto_pm = horas_pm / horas_periodo
    df_inerente_necessaria = df_alvo + impacto_pm
    
    # Verificar se é possível
    if df_inerente_necessaria >= 1.0:
        st.error("❌ **Impossível atingir esta meta!** Mesmo com MTTR zero, a PM sozinha impede atingir esta DF.")
        st.stop()
    
    mttr = (mtbf * (1 - df_inerente_necessaria)) / df_inerente_necessaria
    
    # Exibição
    st.header("📊 Resultado")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("DF Alvo", f"{df_alvo:.2%}")
    
    with col2:
        st.metric("MTBF (entrada)", f"{mtbf:.1f}h")
    
    with col3:
        st.metric("MTTR Máximo", f"{mttr:.1f}h", help="MTTR máximo permitido para atingir a meta")
    
    with col4:
        st.metric("DF Inerente Necessária", f"{df_inerente_necessaria:.2%}", help="Sem considerar PM")
    
    st.divider()
    
    with st.container(border=True):
        st.markdown("### 📐 Cálculo Realizado")
        
        st.markdown(f"**1. Impacto da PM:** {impacto_pm:.2%}")
        st.markdown(f"**2. DF Inerente necessária:** {df_alvo:.2%} + {impacto_pm:.2%} = {df_inerente_necessaria:.2%}")
        
        st.markdown("**3. MTTR máximo:**")
        st.latex(r"MTTR = \frac{MTBF \times (1 - DF_{inerente})}{DF_{inerente}}")
        st.latex(rf"MTTR = \frac{{{mtbf} \times (1 - {df_inerente_necessaria:.4f})}}{{{df_inerente_necessaria:.4f}}} = {mttr:.1f}h")

# ==================== SEÇÃO EDUCATIVA ====================
st.divider()

with st.expander("📚 Conceitos e Definições"):
    st.markdown("""
    ### Disponibilidade Física (DF)
    Percentual do tempo em que o equipamento está fisicamente disponível para operar.
    
    ### DF Inerente vs DF Operacional
    
    **DF Inerente:** Considera apenas falhas aleatórias (MTBF e MTTR)
    - É o "potencial" do equipamento
    - Fórmula: $$DF_{inerente} = \\frac{MTBF}{MTBF + MTTR}$$
    
    **DF Operacional:** Considera falhas + paradas planejadas (PM)
    - É a realidade operacional
    - Fórmula: $$DF_{operacional} = DF_{inerente} - \\frac{Horas_{PM}}{Horas_{período}}$$
    
    ### MTBF (Mean Time Between Failures)
    Tempo médio entre falhas. Quanto **maior**, melhor.
    
    ### MTTR (Mean Time To Repair)
    Tempo médio para reparo. Quanto **menor**, melhor.
    
    ### Manutenção Preventiva (PM)
    Paradas planejadas para manutenção que **reduzem a DF operacional**, mas são necessárias para manter a confiabilidade.
    
    ### Exemplo Prático
    
    Um caminhão com:
    - MTBF = 500h
    - MTTR = 25h
    - PM = 16h/mês
    
    **DF Inerente:**

    $$\\frac{500}{500 + 25} = 95.24\\%$$
    
    **Impacto da PM:**

    $$\\frac{16}{720} = 2.22\\%$$
    
    **DF Operacional:**

    $$95.24\\% - 2.22\\% = 93.02\\%$$
    """)
