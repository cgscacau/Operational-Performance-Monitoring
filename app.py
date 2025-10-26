import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Monitoramento de Performance Operacional",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("Análise de Disponibilidade Física, MTBF, MTTR e Horas de Manutenção Preventiva")

# Sidebar - Configurações
st.sidebar.header("⚙️ Configurações")

# Seleção do modo de cálculo
st.sidebar.subheader("Selecione o modo de cálculo:")
modo_calculo = st.sidebar.radio(
    "Modo:",
    ["📊 Modo Direto (Calcular KPIs)",
     "🎯 Modo Reverso (Atingir Meta DF)",
     "🎲 Simulação e Cenários",
     "📈 Escala MTBF/MTTR vs DF",
     "📚 Análise Histórica"],
    index=0
)

# Relações entre KPIs
st.sidebar.markdown("---")
st.sidebar.subheader("Relações entre KPIs:")
st.sidebar.markdown("""
• DF depende das horas de manutenção
• MTBF depende das horas operadas e falhas
• MTTR depende das horas corretivas e falhas
• Horas operadas = Calendário - Manutenção
""")

# Função para calcular KPIs
def calcular_kpis(horas_calendario, horas_preventiva, horas_corretiva, num_falhas):
    """Calcula os KPIs operacionais"""
    
    # Horas totais de manutenção
    horas_manutencao_total = horas_preventiva + horas_corretiva
    
    # Horas operadas
    horas_operadas = horas_calendario - horas_manutencao_total
    
    # Horas standby
    horas_standby = max(0, horas_calendario - horas_operadas - horas_manutencao_total)
    
    # Disponibilidade Física (DF)
    df = (horas_operadas / horas_calendario * 100) if horas_calendario > 0 else 0
    
    # MTBF (Mean Time Between Failures)
    mtbf = horas_operadas / num_falhas if num_falhas > 0 else 0
    
    # MTTR (Mean Time To Repair)
    mttr = horas_corretiva / num_falhas if num_falhas > 0 else 0
    
    # Taxa Preventiva
    taxa_preventiva = (horas_preventiva / horas_manutencao_total * 100) if horas_manutencao_total > 0 else 0
    
    return {
        'df': df,
        'mtbf': mtbf,
        'mttr': mttr,
        'taxa_preventiva': taxa_preventiva,
        'horas_operadas': horas_operadas,
        'horas_manutencao_total': horas_manutencao_total,
        'horas_preventiva': horas_preventiva,
        'horas_corretiva': horas_corretiva,
        'horas_standby': horas_standby,
        'horas_calendario': horas_calendario
    }

# Função para criar gráfico de gauge
def criar_gauge(valor, titulo, meta, range_max=100, sufixo='%'):
    """Cria um gráfico de gauge para KPIs"""
    
    # Determinar cor baseado na meta
    if valor >= meta:
        cor = 'green'
        status = '✓ Acima da meta'
    else:
        cor = 'red'
        status = '✗ Abaixo da meta'
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=valor,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': titulo, 'font': {'size': 20}},
        delta={'reference': meta, 'increasing': {'color': 'green'}, 'decreasing': {'color': 'red'}},
        number={'suffix': sufixo},
        gauge={
            'axis': {'range': [None, range_max], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': cor},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, meta * 0.8], 'color': 'rgba(255, 0, 0, 0.3)'},
                {'range': [meta * 0.8, meta], 'color': 'rgba(255, 255, 0, 0.3)'},
                {'range': [meta, range_max], 'color': 'rgba(0, 255, 0, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': meta
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="white",
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig, status

# MODO 1: Modo Direto (Calcular KPIs)
if "Modo Direto" in modo_calculo:
    st.header("📊 Dados de Entrada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Metas de Referência")
        meta_df = st.number_input(
            "Meta de DF (%):",
            min_value=0.0,
            max_value=100.0,
            value=85.0,
            step=0.1,
            help="Meta de Disponibilidade Física"
        )
        
        meta_preventiva = st.number_input(
            "Meta Taxa Preventiva (%):",
            min_value=0.0,
            max_value=100.0,
            value=35.0,
            step=0.1,
            help="Meta de Taxa de Manutenção Preventiva"
        )
    
    with col2:
        st.subheader("📅 Período de Análise")
        periodo = st.selectbox(
            "Selecione o período:",
            ["Dia (24h)", "Semana (168h)", "Mês (720h)", "Ano (8760h)", "Personalizado"],
            index=2
        )
        
        if periodo == "Dia (24h)":
            horas_calendario = 24
        elif periodo == "Semana (168h)":
            horas_calendario = 168
        elif periodo == "Mês (720h)":
            horas_calendario = 720
        elif periodo == "Ano (8760h)":
            horas_calendario = 8760
        else:
            horas_calendario = st.number_input(
                "Horas no Calendário:",
                min_value=1.0,
                value=720.0,
                step=1.0
            )
    
    st.markdown("---")
    st.subheader("🔧 Dados de Manutenção")
    
    col1, col2 = st.columns(2)
    
    with col1:
        horas_preventiva = st.number_input(
            "Horas de Manutenção Preventiva:",
            min_value=0.0,
            value=40.0,
            step=1.0,
            help="Total de horas em manutenção preventiva"
        )
    
    with col2:
        num_falhas = st.number_input(
            "Número de Falhas/Quebras:",
            min_value=0,
            value=5,
            step=1,
            help="Quantidade de falhas ou quebras no período"
        )
    
    # Calcular horas corretivas baseado em MTTR estimado
    mttr_estimado = st.slider(
        "MTTR Estimado (horas por falha):",
        min_value=0.5,
        max_value=20.0,
        value=6.0,
        step=0.5,
        help="Tempo médio para reparo por falha"
    )
    
    horas_corretiva = num_falhas * mttr_estimado
    
    st.info(f"📊 Horas Corretivas Calculadas: {horas_corretiva:.2f} h")
    
    # Calcular KPIs
    kpis = calcular_kpis(horas_calendario, horas_preventiva, horas_corretiva, num_falhas)
    
    # Exibir resultados
    st.markdown("---")
    st.header("📈 Resultados dos KPIs")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Disponibilidade Física (DF)",
            f"{kpis['df']:.2f}%",
            f"{kpis['df'] - meta_df:+.2f}% vs meta {meta_df:.2f}%",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "MTTR",
            f"{kpis['mttr']:.2f} h",
            "⚠ 5 reparos" if num_falhas > 0 else "✓ Sem operação"
        )
    
    with col3:
        st.metric(
            "MTBF",
            f"{kpis['mtbf']:.2f} h",
            "✓ Sem operação" if kpis['mtbf'] == 0 else f"↑ {num_falhas} falhas"
        )
    
    with col4:
        st.metric(
            "Taxa Preventiva",
            f"{kpis['taxa_preventiva']:.2f}%",
            f"{kpis['taxa_preventiva'] - meta_preventiva:+.2f}% vs meta {meta_preventiva:.2f}%",
            delta_color="normal"
        )
    
    # Detalhamento
    st.markdown("---")
    st.subheader("📊 Detalhamento:")
    
    detalhamento_df = pd.DataFrame({
        'Métrica': [
            'Horas Calendário',
            'Horas Operadas',
            'Horas Manutenção Total',
            '  • Preventiva',
            '  • Corretiva',
            'Horas Standby'
        ],
        'Valor': [
            f"{kpis['horas_calendario']:.2f} h",
            f"{kpis['horas_operadas']:.2f} h",
            f"{kpis['horas_manutencao_total']:.2f} h",
            f"{kpis['horas_preventiva']:.2f} h",
            f"{kpis['horas_corretiva']:.2f} h",
            f"{kpis['horas_standby']:.2f} h"
        ]
    })
    
    st.dataframe(detalhamento_df, use_container_width=True, hide_index=True)
    
    # Gráficos
    st.markdown("---")
    st.subheader("📊 Visualizações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza - Distribuição de horas
        fig_pizza = go.Figure(data=[go.Pie(
            labels=['Horas Operadas', 'Manutenção Preventiva', 'Manutenção Corretiva', 'Standby'],
            values=[
                kpis['horas_operadas'],
                kpis['horas_preventiva'],
                kpis['horas_corretiva'],
                kpis['horas_standby']
            ],
            hole=0.3,
            marker=dict(colors=['#2ecc71', '#3498db', '#e74c3c', '#95a5a6'])
        )])
        
        fig_pizza.update_layout(
            title={'text': 'Distribuição de Horas', 'x': 0.5, 'xanchor': 'center'},
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col2:
        # Gráfico de barras - Comparação com metas
        fig_barras = go.Figure()
        
        fig_barras.add_trace(go.Bar(
            name='Atual',
            x=['DF (%)', 'Taxa Preventiva (%)'],
            y=[kpis['df'], kpis['taxa_preventiva']],
            marker_color='#3498db'
        ))
        
        fig_barras.add_trace(go.Bar(
            name='Meta',
            x=['DF (%)', 'Taxa Preventiva (%)'],
            y=[meta_df, meta_preventiva],
            marker_color='#2ecc71'
        ))
        
        fig_barras.update_layout(
            title={'text': 'Comparação com Metas', 'x': 0.5, 'xanchor': 'center'},
            barmode='group',
            height=400,
            yaxis_title='Percentual (%)',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig_barras, use_container_width=True)
    
    # Gauges
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_gauge_df, status_df = criar_gauge(kpis['df'], 'Disponibilidade Física', meta_df, 100, '%')
        st.plotly_chart(fig_gauge_df, use_container_width=True)
        st.markdown(f"**Status:** {status_df}")
    
    with col2:
        fig_gauge_prev, status_prev = criar_gauge(
            kpis['taxa_preventiva'],
            'Taxa Preventiva',
            meta_preventiva,
            100,
            '%'
        )
        st.plotly_chart(fig_gauge_prev, use_container_width=True)
        st.markdown(f"**Status:** {status_prev}")

# MODO 2: Modo Reverso
elif "Modo Reverso" in modo_calculo:
    st.header("🎯 Modo Reverso - Atingir Meta de DF")
    
    st.info("💡 Calcule quantas horas de manutenção preventiva são necessárias para atingir a meta de DF desejada.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        meta_df_reverso = st.number_input(
            "Meta de DF Desejada (%):",
            min_value=0.0,
            max_value=100.0,
            value=85.0,
            step=0.1
        )
        
        horas_calendario_reverso = st.number_input(
            "Horas no Calendário:",
            min_value=1.0,
            value=720.0,
            step=1.0
        )
    
    with col2:
        num_falhas_reverso = st.number_input(
            "Número de Falhas Esperadas:",
            min_value=0,
            value=5,
            step=1
        )
        
        mttr_reverso = st.number_input(
            "MTTR por Falha (horas):",
            min_value=0.5,
            value=6.0,
            step=0.5
        )
    
    # Calcular horas preventivas necessárias
    horas_corretiva_reverso = num_falhas_reverso * mttr_reverso
    
    # DF = (Horas Operadas / Horas Calendário) * 100
    # Horas Operadas = Horas Calendário - Horas Preventiva - Horas Corretiva
    # DF/100 = (Horas Calendário - Horas Preventiva - Horas Corretiva) / Horas Calendário
    # Horas Preventiva = Horas Calendário - (DF/100 * Horas Calendário) - Horas Corretiva
    
    horas_preventiva_necessaria = horas_calendario_reverso - (meta_df_reverso/100 * horas_calendario_reverso) - horas_corretiva_reverso
    
    if horas_preventiva_necessaria < 0:
        st.error("⚠️ Não é possível atingir a meta de DF com os parâmetros fornecidos. Reduza o número de falhas ou o MTTR.")
    else:
        st.success(f"✅ Para atingir {meta_df_reverso:.2f}% de DF, você precisa de **{horas_preventiva_necessaria:.2f} horas** de manutenção preventiva.")
        
        # Calcular KPIs resultantes
        kpis_reverso = calcular_kpis(
            horas_calendario_reverso,
            horas_preventiva_necessaria,
            horas_corretiva_reverso,
            num_falhas_reverso
        )
        
        st.markdown("---")
        st.subheader("📊 KPIs Resultantes")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("DF", f"{kpis_reverso['df']:.2f}%")
        
        with col2:
            st.metric("MTBF", f"{kpis_reverso['mtbf']:.2f} h")
        
        with col3:
            st.metric("MTTR", f"{kpis_reverso['mttr']:.2f} h")
        
        with col4:
            st.metric("Taxa Preventiva", f"{kpis_reverso['taxa_preventiva']:.2f}%")

# MODO 3: Simulação e Cenários
elif "Simulação e Cenários" in modo_calculo:
    st.header("🎲 Simulação e Cenários")
    
    st.info("🔬 Varie um parâmetro e veja como os KPIs são afetados.")
    
    # Parâmetro a variar
    parametro_variar = st.selectbox(
        "Variar parâmetro:",
        ["Horas Preventiva", "Número de Falhas", "MTTR", "Horas Calendário"]
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parâmetros Fixos")
        
        if parametro_variar != "Horas Calendário":
            horas_calendario_sim = st.number_input("Horas Calendário:", value=720.0, step=1.0, key="cal_sim")
        
        if parametro_variar != "Horas Preventiva":
            horas_preventiva_sim = st.number_input("Horas Preventiva:", value=40.0, step=1.0, key="prev_sim")
        
        if parametro_variar != "Número de Falhas":
            num_falhas_sim = st.number_input("Número de Falhas:", value=5, step=1, key="falhas_sim")
        
        if parametro_variar != "MTTR":
            mttr_sim = st.number_input("MTTR (h):", value=6.0, step=0.5, key="mttr_sim")
    
    with col2:
        st.subheader("Range de Variação")
        
        if parametro_variar == "Horas Preventiva":
            min_val = st.number_input("Mínimo:", value=10.0, step=1.0)
            max_val = st.number_input("Máximo:", value=100.0, step=1.0)
            valores = np.linspace(min_val, max_val, 20)
        elif parametro_variar == "Número de Falhas":
            min_val = st.number_input("Mínimo:", value=1, step=1)
            max_val = st.number_input("Máximo:", value=20, step=1)
            valores = np.arange(min_val, max_val + 1)
        elif parametro_variar == "MTTR":
            min_val = st.number_input("Mínimo:", value=1.0, step=0.5)
            max_val = st.number_input("Máximo:", value=20.0, step=0.5)
            valores = np.linspace(min_val, max_val, 20)
        else:  # Horas Calendário
            min_val = st.number_input("Mínimo:", value=168.0, step=1.0)
            max_val = st.number_input("Máximo:", value=8760.0, step=1.0)
            valores = np.linspace(min_val, max_val, 20)
    
    # Realizar simulação
    resultados_sim = []
    
    for valor in valores:
        if parametro_variar == "Horas Preventiva":
            kpis_temp = calcular_kpis(
                horas_calendario_sim,
                valor,
                num_falhas_sim * mttr_sim,
                num_falhas_sim
            )
            x_label = valor
        elif parametro_variar == "Número de Falhas":
            kpis_temp = calcular_kpis(
                horas_calendario_sim,
                horas_preventiva_sim,
                valor * mttr_sim,
                int(valor)
            )
            x_label = valor
        elif parametro_variar == "MTTR":
            kpis_temp = calcular_kpis(
                horas_calendario_sim,
                horas_preventiva_sim,
                num_falhas_sim * valor,
                num_falhas_sim
            )
            x_label = valor
        else:  # Horas Calendário
            kpis_temp = calcular_kpis(
                valor,
                horas_preventiva_sim,
                num_falhas_sim * mttr_sim,
                num_falhas_sim
            )
            x_label = valor
        
        resultados_sim.append({
            'x': x_label,
            'df': kpis_temp['df'],
            'mtbf': kpis_temp['mtbf'],
            'mttr': kpis_temp['mttr'],
            'taxa_preventiva': kpis_temp['taxa_preventiva']
        })
    
    df_sim = pd.DataFrame(resultados_sim)
    
    # Gráficos de simulação
    st.markdown("---")
    st.subheader("📈 Resultados da Simulação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_sim_df = go.Figure()
        fig_sim_df.add_trace(go.Scatter(
            x=df_sim['x'],
            y=df_sim['df'],
            mode='lines+markers',
            name='DF',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8)
        ))
        
        fig_sim_df.update_layout(
            title={'text': f'DF vs {parametro_variar}', 'x': 0.5, 'xanchor': 'center'},
            xaxis_title=parametro_variar,
            yaxis_title='Disponibilidade Física (%)',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_sim_df, use_container_width=True)
    
    with col2:
        fig_sim_mtbf = go.Figure()
        fig_sim_mtbf.add_trace(go.Scatter(
            x=df_sim['x'],
            y=df_sim['mtbf'],
            mode='lines+markers',
            name='MTBF',
            line=dict(color='#2ecc71', width=3),
            marker=dict(size=8)
        ))
        
        fig_sim_mtbf.update_layout(
            title={'text': f'MTBF vs {parametro_variar}', 'x': 0.5, 'xanchor': 'center'},
            xaxis_title=parametro_variar,
            yaxis_title='MTBF (horas)',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_sim_mtbf, use_container_width=True)
    
    # Tabela de resultados
    st.markdown("---")
    st.subheader("📋 Tabela de Resultados")
    st.dataframe(df_sim.round(2), use_container_width=True, hide_index=True)

# MODO 4: Escala MTBF/MTTR vs DF
elif "Escala MTBF/MTTR vs DF" in modo_calculo:
    st.header("📈 Escala MTBF/MTTR vs DF")
    
    st.info("📊 Visualize como diferentes combinações de MTBF e MTTR afetam a Disponibilidade Física.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        horas_calendario_escala = st.number_input("Horas Calendário:", value=720.0, step=1.0, key="cal_escala")
        horas_preventiva_escala = st.number_input("Horas Preventiva:", value=40.0, step=1.0, key="prev_escala")
    
    with col2:
        mtbf_range = st.slider("Range de MTBF (horas):", 10, 500, (50, 300), key="mtbf_range")
        mttr_range = st.slider("Range de MTTR (horas):", 1, 50, (2, 20), key="mttr_range")
    
    # Criar grid de valores
    mtbf_valores = np.linspace(mtbf_range[0], mtbf_range[1], 15)
    mttr_valores = np.linspace(mttr_range[0], mttr_range[1], 15)
    
    # Calcular DF para cada combinação
    df_matrix = np.zeros((len(mttr_valores), len(mtbf_valores)))
    
    for i, mttr_val in enumerate(mttr_valores):
        for j, mtbf_val in enumerate(mtbf_valores):
            # Calcular número de falhas baseado em MTBF
            horas_operadas_est = horas_calendario_escala - horas_preventiva_escala
            num_falhas_est = max(1, int(horas_operadas_est / mtbf_val))
            
            # Calcular horas corretivas baseado em MTTR
            horas_corretiva_est = num_falhas_est * mttr_val
            
            # Calcular DF
            kpis_escala = calcular_kpis(
                horas_calendario_escala,
                horas_preventiva_escala,
                horas_corretiva_est,
                num_falhas_est
            )
            
            df_matrix[i, j] = kpis_escala['df']
    
    # Criar heatmap
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=df_matrix,
        x=mtbf_valores,
        y=mttr_valores,
        colorscale='RdYlGn',
        colorbar=dict(title="DF (%)"),
        hovertemplate='MTBF: %{x:.1f}h<br>MTTR: %{y:.1f}h<br>DF: %{z:.2f}%<extra></extra>'
    ))
    
    fig_heatmap.update_layout(
        title={'text': 'Mapa de Calor: MTBF vs MTTR → DF', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='MTBF (horas)',
        yaxis_title='MTTR (horas)',
        height=600
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    st.markdown("""
    **Interpretação:**
    - 🟢 **Verde**: Alta disponibilidade física (DF > 80%)
    - 🟡 **Amarelo**: Disponibilidade moderada (DF 60-80%)
    - 🔴 **Vermelho**: Baixa disponibilidade (DF < 60%)
    
    **Insights:**
    - Aumentar MTBF (mover para direita) melhora a DF
    - Reduzir MTTR (mover para baixo) melhora a DF
    - Melhor região: canto inferior direito (alto MTBF, baixo MTTR)
    """)

# MODO 5: Análise Histórica
elif "Análise Histórica" in modo_calculo:
    st.header("📚 Análise Histórica")
    
    st.info("📅 Analise a evolução dos KPIs ao longo do tempo.")
    
    # Opção de upload de arquivo
    uploaded_file = st.file_uploader("Carregue um arquivo CSV ou Excel com dados históricos", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_historico = pd.read_csv(uploaded_file)
            else:
                df_historico = pd.read_excel(uploaded_file)
            
            st.success("✅ Arquivo carregado com sucesso!")
            
            # Mostrar preview dos dados
            st.subheader("📋 Preview dos Dados")
            st.dataframe(df_historico.head(), use_container_width=True)
            
            # Verificar colunas necessárias
            colunas_necessarias = ['data', 'horas_calendario', 'horas_preventiva', 'horas_corretiva', 'num_falhas']
            colunas_faltantes = [col for col in colunas_necessarias if col not in df_historico.columns]
            
            if colunas_faltantes:
                st.error(f"⚠️ Colunas faltantes: {', '.join(colunas_faltantes)}")
                st.info("O arquivo deve conter as colunas: data, horas_calendario, horas_preventiva, horas_corretiva, num_falhas")
            else:
                # Converter data
                df_historico['data'] = pd.to_datetime(df_historico['data'])
                
                # Calcular KPIs para cada linha
                kpis_historicos = []
                for _, row in df_historico.iterrows():
                    kpis_temp = calcular_kpis(
                        row['horas_calendario'],
                        row['horas_preventiva'],
                        row['horas_corretiva'],
                        row['num_falhas']
                    )
                    kpis_historicos.append(kpis_temp)
                
                df_kpis = pd.DataFrame(kpis_historicos)
                df_historico = pd.concat([df_historico, df_kpis], axis=1)
                
                # Gráficos de evolução
                st.markdown("---")
                st.subheader("📈 Evolução dos KPIs")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_evolucao_df = go.Figure()
                    fig_evolucao_df.add_trace(go.Scatter(
                        x=df_historico['data'],
                        y=df_historico['df'],
                        mode='lines+markers',
                        name='DF',
                        line=dict(color='#3498db', width=2),
                        marker=dict(size=6)
                    ))
                    
                    fig_evolucao_df.update_layout(
                        title={'text': 'Evolução da Disponibilidade Física', 'x': 0.5, 'xanchor': 'center'},
                        xaxis_title='Data',
                        yaxis_title='DF (%)',
                        height=400,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_evolucao_df, use_container_width=True)
                
                with col2:
                    fig_evolucao_mtbf = go.Figure()
                    fig_evolucao_mtbf.add_trace(go.Scatter(
                        x=df_historico['data'],
                        y=df_historico['mtbf'],
                        mode='lines+markers',
                        name='MTBF',
                        line=dict(color='#2ecc71', width=2),
                        marker=dict(size=6)
                    ))
                    
                    fig_evolucao_mtbf.update_layout(
                        title={'text': 'Evolução do MTBF', 'x': 0.5, 'xanchor': 'center'},
                        xaxis_title='Data',
                        yaxis_title='MTBF (horas)',
                        height=400,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_evolucao_mtbf, use_container_width=True)
                
                # Estatísticas resumidas
                st.markdown("---")
                st.subheader("📊 Estatísticas Resumidas")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("DF Médio", f"{df_historico['df'].mean():.2f}%")
                    st.metric("DF Mínimo", f"{df_historico['df'].min():.2f}%")
                
                with col2:
                    st.metric("MTBF Médio", f"{df_historico['mtbf'].mean():.2f} h")
                    st.metric("MTBF Máximo", f"{df_historico['mtbf'].max():.2f} h")
                
                with col3:
                    st.metric("MTTR Médio", f"{df_historico['mttr'].mean():.2f} h")
                    st.metric("MTTR Mínimo", f"{df_historico['mttr'].min():.2f} h")
                
                with col4:
                    st.metric("Taxa Prev. Média", f"{df_historico['taxa_preventiva'].mean():.2f}%")
                    st.metric("Total de Falhas", f"{df_historico['num_falhas'].sum()}")
                
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")
    
    else:
        st.warning("📁 Faça upload de um arquivo para começar a análise histórica.")
        
        st.markdown("""
        **Formato esperado do arquivo:**
        
        | data       | horas_calendario | horas_preventiva | horas_corretiva | num_falhas |
        |------------|------------------|------------------|-----------------|------------|
        | 2024-01-01 | 720              | 40               | 30              | 5          |
        | 2024-02-01 | 720              | 45               | 25              | 4          |
        | ...        | ...              | ...              | ...             | ...        |
        """)

# Rodapé
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d;'>
    <p>📊 Sistema de Monitoramento de Performance Operacional</p>
    <p>Desenvolvido para análise de KPIs industriais</p>
</div>
""", unsafe_allow_html=True)
