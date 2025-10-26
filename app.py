# app.py

import streamlit as st

# ==================== CONFIGURAÇÃO ====================
st.set_page_config(
    page_title="Calculadora de Disponibilidade",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Calculadora de Disponibilidade Física (DF)")
st.markdown("Relacione DF, MTBF, MTTR e MTBS de forma simples e direta.")

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

# ==================== ENTRADAS BASEADAS NO MODO ====================

if modo == "Calcular DF (tenho MTBF e MTTR)":
    st.sidebar.subheader("Dados de Entrada")
    
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
    
    # Cálculo
    df = mtbf / (mtbf + mttr)
    
    # Exibição
    st.header("📊 Resultado")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("MTBF (entrada)", f"{mtbf:.1f}h")
    
    with col2:
        st.metric("MTTR (entrada)", f"{mttr:.1f}h")
    
    with col3:
        st.metric("DF (calculado)", f"{df:.2%}", help="Disponibilidade Física")
    
    st.divider()
    
    # Explicação
    with st.container(border=True):
        st.markdown("### 📐 Cálculo Realizado")
        st.latex(r"DF = \frac{MTBF}{MTBF + MTTR}")
        st.latex(rf"DF = \frac{{{mtbf}}}{{{mtbf} + {mttr}}} = {df:.4f} = {df:.2%}")

elif modo == "Calcular MTBF (tenho DF e MTTR)":
    st.sidebar.subheader("Dados de Entrada")
    
    df = st.sidebar.number_input(
        "DF (%)",
        min_value=0.1,
        max_value=99.9,
        value=95.0,
        step=0.1,
        help="Disponibilidade Física alvo"
    ) / 100
    
    mttr = st.sidebar.number_input(
        "MTTR (horas)",
        min_value=0.1,
        value=25.0,
        step=1.0,
        help="Tempo Médio Para Reparo"
    )
    
    # Cálculo
    mtbf = (mttr * df) / (1 - df)
    
    # Exibição
    st.header("📊 Resultado")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("DF (entrada)", f"{df:.2%}")
    
    with col2:
        st.metric("MTTR (entrada)", f"{mttr:.1f}h")
    
    with col3:
        st.metric("MTBF (calculado)", f"{mtbf:.1f}h", help="Tempo Médio Entre Falhas necessário")
    
    st.divider()
    
    # Explicação
    with st.container(border=True):
        st.markdown("### 📐 Cálculo Realizado")
        st.markdown("Partindo da fórmula:")
        st.latex(r"DF = \frac{MTBF}{MTBF + MTTR}")
        st.markdown("Isolando MTBF:")
        st.latex(r"MTBF = \frac{MTTR \times DF}{1 - DF}")
        st.latex(rf"MTBF = \frac{{{mttr} \times {df:.4f}}}{{1 - {df:.4f}}} = {mtbf:.1f}h")

elif modo == "Calcular MTTR (tenho DF e MTBF)":
    st.sidebar.subheader("Dados de Entrada")
    
    df = st.sidebar.number_input(
        "DF (%)",
        min_value=0.1,
        max_value=99.9,
        value=95.0,
        step=0.1,
        help="Disponibilidade Física alvo"
    ) / 100
    
    mtbf = st.sidebar.number_input(
        "MTBF (horas)",
        min_value=0.1,
        value=500.0,
        step=10.0,
        help="Tempo Médio Entre Falhas"
    )
    
    # Cálculo
    mttr = (mtbf * (1 - df)) / df
    
    # Exibição
    st.header("📊 Resultado")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("DF (entrada)", f"{df:.2%}")
    
    with col2:
        st.metric("MTBF (entrada)", f"{mtbf:.1f}h")
    
    with col3:
        st.metric("MTTR (calculado)", f"{mttr:.1f}h", help="Tempo Médio Para Reparo necessário")
    
    st.divider()
    
    # Explicação
    with st.container(border=True):
        st.markdown("### 📐 Cálculo Realizado")
        st.markdown("Partindo da fórmula:")
        st.latex(r"DF = \frac{MTBF}{MTBF + MTTR}")
        st.markdown("Isolando MTTR:")
        st.latex(r"MTTR = \frac{MTBF \times (1 - DF)}{DF}")
        st.latex(rf"MTTR = \frac{{{mtbf} \times (1 - {df:.4f})}}{{{df:.4f}}} = {mttr:.1f}h")

# ==================== SEÇÃO EDUCATIVA ====================
st.divider()

with st.expander("📚 Conceitos e Definições"):
    st.markdown("""
    ### Disponibilidade Física (DF)
    Percentual do tempo em que o equipamento está fisicamente disponível para operar (não quebrado, não em reparo).
    
    ### MTBF (Mean Time Between Failures)
    Tempo médio entre falhas consecutivas. Quanto **maior**, melhor a confiabilidade do equipamento.
    
    **Exemplo:** MTBF = 500h significa que, em média, o equipamento opera 500 horas antes de falhar.
    
    ### MTTR (Mean Time To Repair)
    Tempo médio necessário para reparar o equipamento após uma falha. Quanto **menor**, melhor a manutenabilidade.
    
    **Exemplo:** MTTR = 25h significa que, em média, leva 25 horas para consertar o equipamento.
    
    ### MTBS (Mean Time Between Services)
    Tempo médio entre manutenções preventivas programadas. Usado para planejar paradas de manutenção.
    
    ### Relação entre os Conceitos
    
    A fórmula fundamental da disponibilidade é:

    
    $$DF = \\frac{MTBF}{MTBF + MTTR}$$
    
    Isso significa que a disponibilidade depende de:
    - **Confiabilidade** (MTBF): quanto tempo funciona sem falhar
    - **Manutenabilidade** (MTTR): quanto tempo leva para consertar
    
    ### Exemplo Prático
    
    Um caminhão com:
    - MTBF = 500h (funciona 500h entre falhas)
    - MTTR = 25h (leva 25h para consertar)
    
    Terá uma disponibilidade de:

    $$DF = \\frac{500}{500 + 25} = \\frac{500}{525} = 0.9524 = 95.24\\%$$
    
    Isso significa que, em média, o caminhão estará disponível 95.24% do tempo.
    """)

with st.expander("🔄 Como usar esta calculadora"):
    st.markdown("""
    ### Cenário 1: Quero saber a DF atual
    **Situação:** Tenho dados de MTBF e MTTR do meu equipamento.
    
    **Passos:**
    1. Selecione "Calcular DF (tenho MTBF e MTTR)"
    2. Insira os valores de MTBF e MTTR
    3. Veja a DF resultante
    
    ---
    
    ### Cenário 2: Tenho uma meta de DF e quero saber o MTBF necessário
    **Situação:** Minha meta é DF = 95% e sei que meu MTTR = 25h.
    
    **Passos:**
    1. Selecione "Calcular MTBF (tenho DF e MTTR)"
    2. Insira DF = 95% e MTTR = 25h
    3. Veja qual MTBF você precisa atingir
    
    ---
    
    ### Cenário 3: Tenho uma meta de DF e quero saber o MTTR necessário
    **Situação:** Minha meta é DF = 95% e sei que meu MTBF = 500h.
    
    **Passos:**
    1. Selecione "Calcular MTTR (tenho DF e MTBF)"
    2. Insira DF = 95% e MTBF = 500h
    3. Veja qual MTTR máximo você pode ter
    """)
