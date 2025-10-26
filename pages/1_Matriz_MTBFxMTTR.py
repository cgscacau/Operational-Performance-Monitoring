# pages/1_Matriz_MTBFxMTTR.py

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from core import df_from_mtbf_mttr

st.set_page_config(layout="wide")

st.title("🗺️ Matriz Interativa MTBF × MTTR ↔ DF")
st.markdown("Explore a relação entre confiabilidade (MTBF), manutenabilidade (MTTR) e a Disponibilidade Física (DF) resultante.")

# --- Pegar os valores da página principal se existirem ---
# Usar st.session_state seria mais robusto, mas para este MVP, vamos usar inputs locais
# para manter a página autocontida.

col1, col2 = st.columns(2)
with col1:
    mtbf_atual = st.number_input("Seu MTBF atual (h)", min_value=1, value=500, key="mtbf_matriz")
with col2:
    mttr_atual = st.number_input("Seu MTTR atual (h)", min_value=1, value=25, key="mttr_matriz")

df_meta_matriz = st.slider("Selecione a DF Meta para visualizar a fronteira", 0.80, 0.99, 0.92, 0.01, format="%.2f%%")

# --- Geração dos dados para o gráfico ---
mtbf_range = np.linspace(max(1, mtbf_atual * 0.2), mtbf_atual * 2, 50)
mttr_range = np.linspace(max(1, mttr_atual * 0.2), mttr_atual * 2, 50)

# Criar uma grade de pontos
X_mtbf, Y_mttr = np.meshgrid(mtbf_range, mttr_range)

# Calcular a DF para cada ponto da grade
Z_df = df_from_mtbf_mttr(X_mtbf, Y_mttr)

# --- Criação do Gráfico com Plotly ---
fig = go.Figure()

# Adicionar as linhas de contorno (isolinhas de DF)
contour = fig.add_trace(go.Contour(
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

# Adicionar a linha de fronteira da meta
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

# Adicionar o ponto da situação atual
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

# --- Layout do Gráfico ---
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
