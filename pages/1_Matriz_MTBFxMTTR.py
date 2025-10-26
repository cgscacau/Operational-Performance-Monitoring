# pages/1_Matriz_MTBFxMTTR.py

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from core import df_from_mtbf_mttr

st.set_page_config(layout="wide", page_icon="🗺️")

# --- INICIALIZAÇÃO DO SESSION STATE (CÓPIA DA PÁGINA PRINCIPAL) ---
# <<< MUDANÇA CRÍTICA AQUI
# Isso garante que, mesmo que o usuário abra esta página primeiro,
# os valores padrão serão carregados e o app não vai quebrar.
if 'df_meta' not in st.session_state:
    st.session_state.df_meta = 0.92
if 'uf_meta' not in st.session_state:
    st.session_state.uf_meta = 0.85
if 'mtbf' not in st.session_state:
    st.session_state.mtbf = 500
if 'mttr' not in st.session_state:
    st.session_state.mttr = 25
if 'pm_downtime_mensal' not in st.session_state:
    st.session_state.pm_downtime_mensal = 8

# --- Título da Página ---
st.title("🗺️ Matriz Interativa MTBF × MTTR ↔ DF")
st.markdown("Explore a relação entre confiabilidade (MTBF), manutenabilidade (MTTR) e a Disponibilidade Física (DF) resultante.")

# --- Ler os valores diretamente do session_state ---
# Agora podemos remover a verificação de 'st.stop()' porque garantimos que os valores sempre existirão.
mtbf_atual = st.session_state.mtbf
mttr_atual = st.session_state.mttr
df_meta_matriz = st.session_state.df_meta

# Adicionamos uma nota para o usuário saber de onde vêm os dados
st.info(f"O gráfico está usando os valores definidos na barra lateral: **MTBF = {mtbf_atual}h**, **MTTR = {mttr_atual}h**, **Meta DF = {df_meta_matriz:.2%}**.")

# --- Geração dos dados para o gráfico ---
mtbf_range = np.linspace(max(1, mtbf_atual * 0.2), mtbf_atual * 2, 50)
mttr_range = np.linspace(max(1, mttr_atual * 0.2), mttr_atual * 2, 50)

X_mtbf, Y_mttr = np.meshgrid(mtbf_range, mttr_range)
Z_df = df_from_mtbf_mttr(X_mtbf, Y_mttr)

# --- Criação do Gráfico com Plotly ---
fig = go.Figure()

fig.add_trace(go.Contour(
    z=Z_df,
    x=mtbf_range,
    y=mttr_range,
    colorscale='Viridis',
    contours_coloring='lines',
    line_width=2,
    contours=dict(
        start=0.8,
        end=0.99,
        size=0.01,
        showlabels=True,
        labelfont=dict(size=12, color='black')
    ),
    name='Isolinhas de DF'
))

fig.add_trace(go.Contour(
    z=Z_df,
    x=mtbf_range,
    y=mttr_range,
    contours_coloring='none',
    line_width=4,
    line_color='red',
    contours=dict(
        type='constraint',
        value=df_meta_matriz,
    ),
    name=f'Fronteira para {df_meta_matriz:.1%}'
))

df_atual = df_from_mtbf_mttr(mtbf_atual, mttr_atual)
fig.add_trace(go.Scatter(
    x=[mtbf_atual],
    y=[mttr_atual],
    mode='markers+text',
    marker=dict(color='red', size=15, symbol='x'),
    text=[f"Atual: {df_atual:.2%}"],
    textposition="bottom right",
    name='Situação Atual'
))

fig.update_layout(
    title=f'Fronteira de Viabilidade para Atingir {df_meta_matriz:.1%} de DF',
    xaxis_title="MTBF (horas) → Melhor Confiabilidade",
    yaxis_title="MTTR (horas) → Melhor Manutenabilidade",
    autosize=True,
    height=600,
    xaxis=dict(gridcolor='lightgrey'),
    yaxis=dict(gridcolor='lightgrey'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    f"**Como ler o gráfico:** Qualquer combinação de MTBF e MTTR na área verde-claro (acima da linha vermelha) atinge a meta de **{df_meta_matriz:.1%}**. "
    f"Seu ponto atual está marcado com um 'X'. Para cruzar a fronteira, você precisa se mover para a direita (aumentar MTBF) ou para baixo (diminuir MTTR)."
)
