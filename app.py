# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==================== CONFIGURAÇÃO ====================
st.set_page_config(
    page_title="Matriz de Viabilidade DF",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Matriz de Viabilidade: MTBF × MTTR → DF")
st.markdown("Descubra quais combinações de MTBF e MTTR atingem sua meta de DF, considerando as horas de manutenção preventiva.")

# ==================== INPUTS ====================
st.sidebar.header("⚙️ Configuração")

st.sidebar.subheader("Meta de Disponibilidade")
df_meta = st.sidebar.slider(
    "Meta de DF (%)",
    min_value=80.0,
    max_value=99.0,
    value=92.0,
    step=0.5,
    help="Disponibilidade Física alvo"
)

st.sidebar.divider()

st.sidebar.subheader("⏱️ Período de Análise")
periodo = st.sidebar.selectbox(
    "Período",
    ["Mensal (30 dias)", "Anual (365 dias)"],
    help="Período para análise"
)

if periodo == "Mensal (30 dias)":
    horas_periodo = 30 * 24
else:
    horas_periodo = 365 * 24

st.sidebar.info(f"📅 **{horas_periodo}h** ({horas_periodo/24:.0f} dias)")

st.sidebar.divider()

st.sidebar.subheader("🔧 Manutenção Preventiva")
horas_pm = st.sidebar.number_input(
    f"Horas de PM no período",
    min_value=0.0,
    value=16.0 if periodo == "Mensal (30 dias)" else 192.0,
    step=1.0,
    help="Total de horas de parada para PM"
)

st.sidebar.divider()

st.sidebar.subheader("📊 Faixas da Matriz")
mtbf_min = st.sidebar.number_input("MTBF Mínimo (h)", min_value=10, value=100, step=10)
mtbf_max = st.sidebar.number_input("MTBF Máximo (h)", min_value=mtbf_min+10, value=1000, step=10)
mttr_min = st.sidebar.number_input("MTTR Mínimo (h)", min_value=1, value=5, step=1)
mttr_max = st.sidebar.number_input("MTTR Máximo (h)", min_value=mttr_min+1, value=50, step=1)

# ==================== CÁLCULOS ====================

# Converter meta para decimal
df_meta_decimal = df_meta / 100

# Calcular impacto da PM
impacto_pm = horas_pm / horas_periodo

# DF Inerente necessária (antes de descontar PM)
df_inerente_necessaria = df_meta_decimal + impacto_pm

# Verificar viabilidade
if df_inerente_necessaria >= 1.0:
    st.error(f"❌ **Meta Impossível!** Com {horas_pm}h de PM no período, mesmo com equipamento perfeito (sem falhas), "
             f"a DF máxima seria {(1 - impacto_pm):.2%}. Reduza as horas de PM ou a meta de DF.")
    st.stop()

# Criar grade de valores
mtbf_range = np.linspace(mtbf_min, mtbf_max, 100)
mttr_range = np.linspace(mttr_min, mttr_max, 100)

# Criar meshgrid
MTBF, MTTR = np.meshgrid(mtbf_range, mttr_range)

# Calcular DF Inerente para cada combinação
DF_inerente = MTBF / (MTBF + MTTR)

# Calcular DF Operacional (descontando PM)
DF_operacional = DF_inerente - impacto_pm

# ==================== EXIBIÇÃO ====================

# Métricas principais
st.header("📊 Análise da Meta")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Meta de DF",
        f"{df_meta_decimal:.2%}",
        help="Disponibilidade Física alvo"
    )

with col2:
    st.metric(
        "Horas de PM",
        f"{horas_pm:.0f}h",
        help="Paradas planejadas no período"
    )

with col3:
    st.metric(
        "Impacto da PM",
        f"{impacto_pm:.2%}",
        delta=f"-{impacto_pm:.2%}",
        delta_color="inverse",
        help="Redução da DF devido à PM"
    )

with col4:
    st.metric(
        "DF Inerente Necessária",
        f"{df_inerente_necessaria:.2%}",
        help="DF sem PM para atingir a meta"
    )

st.divider()

# ==================== GRÁFICO INTERATIVO ====================
st.subheader("🗺️ Matriz de Viabilidade")

fig = go.Figure()

# Adicionar mapa de calor com DF Operacional
fig.add_trace(go.Contour(
    z=DF_operacional,
    x=mtbf_range,
    y=mttr_range,
    colorscale='RdYlGn',
    contours_coloring='heatmap',
    colorbar=dict(
        title="DF Operacional",
        tickformat='.0%'
    ),
    hovertemplate='MTBF: %{x:.0f}h<br>MTTR: %{y:.0f}h<br>DF: %{z:.2%}<extra></extra>',
    name='DF Operacional'
))

# Adicionar linha de contorno da meta
fig.add_trace(go.Contour(
    z=DF_operacional,
    x=mtbf_range,
    y=mttr_range,
    contours_coloring='lines',
    contours=dict(
        start=df_meta_decimal,
        end=df_meta_decimal,
        size=0.01,
        showlabels=True,
        labelfont=dict(size=14, color='red', family='Arial Black')
    ),
    line=dict(color='red', width=4),
    showscale=False,
    hoverinfo='skip',
    name=f'Meta: {df_meta:.1f}%'
))

fig.update_layout(
    title=f'Combinações de MTBF e MTTR para atingir {df_meta:.1f}% de DF<br><sub>Considerando {horas_pm:.0f}h de PM</sub>',
    xaxis_title='MTBF (horas) → Melhor Confiabilidade',
    yaxis_title='MTTR (horas) → Pior Manutenabilidade',
    height=600,
    hovermode='closest'
)

st.plotly_chart(fig, use_container_width=True)

# Legenda do gráfico
st.info("""
**Como interpretar o gráfico:**
- 🟢 **Região Verde:** Combinações que **ATINGEM** a meta de DF
- 🔴 **Região Vermelha:** Combinações que **NÃO ATINGEM** a meta
- **Linha Vermelha Grossa:** Fronteira exata da meta (todas as combinações nesta linha resultam exatamente na DF alvo)

**Estratégia:**
- Para **melhorar confiabilidade:** mova para a direita (aumentar MTBF)
- Para **melhorar manutenabilidade:** mova para baixo (reduzir MTTR)
""")

st.divider()

# ==================== TABELA DE CENÁRIOS ====================
st.subheader("📋 Cenários Específicos")

st.markdown("Exemplos de combinações que atingem sua meta:")

# Calcular alguns cenários específicos
cenarios = []

# Cenário 1: MTTR baixo
mttr_otimo = 10
mtbf_necessario_1 = (mttr_otimo * df_inerente_necessaria) / (1 - df_inerente_necessaria)
cenarios.append({
    'Cenário': 'Manutenibilidade Excelente',
    'MTBF (h)': f"{mtbf_necessario_1:.0f}",
    'MTTR (h)': f"{mttr_otimo:.0f}",
    'Estratégia': 'Equipe ágil, peças disponíveis'
})

# Cenário 2: MTBF alto
mtbf_otimo = 800
mttr_permitido_1 = (mtbf_otimo * (1 - df_inerente_necessaria)) / df_inerente_necessaria
cenarios.append({
    'Cenário': 'Confiabilidade Excelente',
    'MTBF (h)': f"{mtbf_otimo:.0f}",
    'MTTR (h)': f"{mttr_permitido_1:.0f}",
    'Estratégia': 'Equipamento robusto, poucas falhas'
})

# Cenário 3: Balanceado
mtbf_balanceado = 500
mttr_balanceado = (mtbf_balanceado * (1 - df_inerente_necessaria)) / df_inerente_necessaria
cenarios.append({
    'Cenário': 'Balanceado',
    'MTBF (h)': f"{mtbf_balanceado:.0f}",
    'MTTR (h)': f"{mttr_balanceado:.0f}",
    'Estratégia': 'Equilíbrio entre confiabilidade e manutenção'
})

df_cenarios = pd.DataFrame(cenarios)
st.dataframe(df_cenarios, use_container_width=True, hide_index=True)

st.divider()

# ==================== ANÁLISE DE SENSIBILIDADE ====================
st.subheader("🔬 Análise de Sensibilidade")

col_sens1, col_sens2 = st.columns(2)

with col_sens1:
    st.markdown("### Se eu reduzir o MTTR em 20%...")
    
    mttr_exemplo = 30
    mtbf_necessario_atual = (mttr_exemplo * df_inerente_necessaria) / (1 - df_inerente_necessaria)
    
    mttr_reduzido = mttr_exemplo * 0.8
    mtbf_necessario_novo = (mttr_reduzido * df_inerente_necessaria) / (1 - df_inerente_necessaria)
    
    reducao_mtbf = mtbf_necessario_atual - mtbf_necessario_novo
    
    st.markdown(f"**Exemplo:** MTTR de {mttr_exemplo}h → {mttr_reduzido:.0f}h")
    st.markdown(f"**MTBF necessário cai:** {mtbf_necessario_atual:.0f}h → {mtbf_necessario_novo:.0f}h")
    st.success(f"💡 Você pode **relaxar** o MTBF em **{reducao_mtbf:.0f}h** ({reducao_mtbf/mtbf_necessario_atual*100:.1f}%)")

with col_sens2:
    st.markdown("### Se eu aumentar o MTBF em 20%...")
    
    mtbf_exemplo = 500
    mttr_permitido_atual = (mtbf_exemplo * (1 - df_inerente_necessaria)) / df_inerente_necessaria
    
    mtbf_aumentado = mtbf_exemplo * 1.2
    mttr_permitido_novo = (mtbf_aumentado * (1 - df_inerente_necessaria)) / df_inerente_necessaria
    
    aumento_mttr = mttr_permitido_novo - mttr_permitido_atual
    
    st.markdown(f"**Exemplo:** MTBF de {mtbf_exemplo}h → {mtbf_aumentado:.0f}h")
    st.markdown(f"**MTTR permitido sobe:** {mttr_permitido_atual:.0f}h → {mttr_permitido_novo:.0f}h")
    st.success(f"💡 Você pode **tolerar** MTTR até **{aumento_mttr:.0f}h** maior ({aumento_mttr/mttr_permitido_atual*100:.1f}%)")

st.divider()

# ==================== CALCULADORA RÁPIDA ====================
with st.expander("🧮 Calculadora Rápida: Qual MTBF/MTTR eu preciso?"):
    calc_col1, calc_col2 = st.columns(2)
    
    with calc_col1:
        st.markdown("### Tenho MTTR, preciso de MTBF")
        mttr_input = st.number_input("MTTR (h)", min_value=1.0, value=25.0, step=1.0, key='calc1')
        mtbf_resultado = (mttr_input * df_inerente_necessaria) / (1 - df_inerente_necessaria)
        st.metric("MTBF Necessário", f"{mtbf_resultado:.0f}h")
    
    with calc_col2:
        st.markdown("### Tenho MTBF, preciso de MTTR")
        mtbf_input = st.number_input("MTBF (h)", min_value=10.0, value=500.0, step=10.0, key='calc2')
        mttr_resultado = (mtbf_input * (1 - df_inerente_necessaria)) / df_inerente_necessaria
        st.metric("MTTR Máximo", f"{mttr_resultado:.0f}h")

# ==================== EXPLICAÇÃO ====================
with st.expander("📚 Entenda os Cálculos"):
    st.markdown(f"""
    ### Passo a Passo
    
    **1. Sua Meta:** DF Operacional = {df_meta:.1f}%
    
    **2. Impacto da PM:**
    - Horas de PM: {horas_pm:.0f}h
    - Horas do período: {horas_periodo:.0f}h
    - Impacto: {horas_pm:.0f} / {horas_periodo:.0f} = {impacto_pm:.2%}
    
    **3. DF Inerente Necessária:**
    - Para ter {df_meta:.1f}% operacional, preciso de {df_inerente_necessaria:.2%} inerente
    - Fórmula: DF_inerente = DF_meta + Impacto_PM
    - Cálculo: {df_meta_decimal:.4f} + {impacto_pm:.4f} = {df_inerente_necessaria:.4f}
    
    **4. Relação MTBF × MTTR:**
    
    Da fórmula básica:

    $$DF = \\frac{{MTBF}}{{MTBF + MTTR}}$$
    
    Isolando MTBF:

    $$MTBF = \\frac{{MTTR \\times DF}}{{1 - DF}}$$
    
    Isolando MTTR:

    $$MTTR = \\frac{{MTBF \\times (1 - DF)}}{{DF}}$$
    
    **Exemplo:**
    - Se MTTR = 25h e DF necessária = {df_inerente_necessaria:.2%}
    - MTBF = (25 × {df_inerente_necessaria:.4f}) / (1 - {df_inerente_necessaria:.4f})
    - MTBF = {(25 * df_inerente_necessaria) / (1 - df_inerente_necessaria):.0f}h
    """)
