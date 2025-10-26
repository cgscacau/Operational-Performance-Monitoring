import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Calculadora de KPIs de Confiabilidade",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    h1 {
        color: #1f77b4;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("🔧 Calculadora de KPIs de Confiabilidade de Frotas")
st.markdown("**Análise de Disponibilidade Física, MTBF, MTTR e Horas de Manutenção Preventiva**")
st.markdown("---")

# Funções de cálculo
def calcular_disponibilidade_fisica(horas_calendario, horas_manutencao_corretiva, horas_manutencao_preventiva):
    """
    DF = (Horas Calendário - Horas Manutenção Total) / Horas Calendário × 100%
    """
    horas_manutencao_total = horas_manutencao_corretiva + horas_manutencao_preventiva
    if horas_calendario > 0:
        df = ((horas_calendario - horas_manutencao_total) / horas_calendario) * 100
        return max(0, min(100, df))  # Limita entre 0 e 100
    return 0

def calcular_mtbf(horas_operadas, numero_falhas):
    """
    MTBF = Horas Operadas / Número de Falhas
    """
    if numero_falhas > 0:
        return horas_operadas / numero_falhas
    return float('inf')

def calcular_mttr(horas_manutencao_corretiva, numero_falhas):
    """
    MTTR = Horas de Manutenção Corretiva / Número de Falhas
    """
    if numero_falhas > 0:
        return horas_manutencao_corretiva / numero_falhas
    return 0

def calcular_horas_operadas(horas_calendario, horas_manutencao_total, horas_standby=0):
    """
    Horas Operadas = Horas Calendário - Horas Manutenção - Horas Standby
    """
    return max(0, horas_calendario - horas_manutencao_total - horas_standby)

def calcular_numero_falhas_de_mtbf(horas_operadas, mtbf_alvo):
    """
    Número de Falhas = Horas Operadas / MTBF
    """
    if mtbf_alvo > 0:
        return horas_operadas / mtbf_alvo
    return 0

def calcular_horas_corretiva_de_mttr(numero_falhas, mttr_alvo):
    """
    Horas Corretiva = Número de Falhas × MTTR
    """
    return numero_falhas * mttr_alvo

def calcular_taxa_preventiva(horas_preventiva, horas_manutencao_total):
    """
    % Preventiva = (Horas Preventiva / Total Manutenção) × 100%
    """
    if horas_manutencao_total > 0:
        return (horas_preventiva / horas_manutencao_total) * 100
    return 0

# Sidebar - Modo de cálculo
st.sidebar.header("⚙️ Configurações")
modo_calculo = st.sidebar.radio(
    "Selecione o modo de cálculo:",
    ["📊 Modo Direto (Calcular KPIs)", 
     "🎯 Modo Reverso (Atingir Meta DF)",
     "📈 Simulação e Cenários",
     "📋 Análise Histórica"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Relações entre KPIs:**
- DF depende das horas de manutenção
- MTBF depende das horas operadas e falhas
- MTTR depende das horas corretivas e falhas
- Horas operadas = Calendário - Manutenção
""")

# ========== MODO DIRETO ==========
if modo_calculo == "📊 Modo Direto (Calcular KPIs)":
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Dados de Entrada")
        
        # Período de análise
        st.markdown("**Período de Análise**")
        periodo = st.selectbox(
            "Selecione o período:",
            ["Dia (24h)", "Semana (168h)", "Mês (720h)", "Ano (8760h)", "Personalizado"]
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
            horas_calendario = st.number_input("Horas Calendário:", min_value=1.0, value=720.0, step=1.0)
        
        st.markdown("**Dados de Manutenção**")
        horas_preventiva = st.number_input(
            "Horas de Manutenção Preventiva:", 
            min_value=0.0, 
            value=40.0, 
            step=1.0,
            help="Total de horas gastas em manutenções programadas"
        )
        
        numero_falhas = st.number_input(
            "Número de Falhas/Quebras:", 
            min_value=0, 
            value=5, 
            step=1,
            help="Quantidade de falhas no período"
        )
        
        horas_corretiva = st.number_input(
            "Horas de Manutenção Corretiva:", 
            min_value=0.0, 
            value=30.0, 
            step=1.0,
            help="Total de horas gastas em reparos não programados"
        )
        
        horas_standby = st.number_input(
            "Horas em Standby (opcional):", 
            min_value=0.0, 
            value=0.0, 
            step=1.0,
            help="Horas que o equipamento ficou parado aguardando operação"
        )
    
    with col2:
        st.subheader("📊 Resultados dos KPIs")
        
        # Cálculos
        horas_manutencao_total = horas_preventiva + horas_corretiva
        horas_operadas = calcular_horas_operadas(horas_calendario, horas_manutencao_total, horas_standby)
        df_resultado = calcular_disponibilidade_fisica(horas_calendario, horas_corretiva, horas_preventiva)
        mtbf_resultado = calcular_mtbf(horas_operadas, numero_falhas)
        mttr_resultado = calcular_mttr(horas_corretiva, numero_falhas)
        taxa_preventiva = calcular_taxa_preventiva(horas_preventiva, horas_manutencao_total)
        
        # Métricas principais
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(
                "Disponibilidade Física (DF)", 
                f"{df_resultado:.2f}%",
                delta=f"{df_resultado - 85:.2f}% vs meta 85%" if df_resultado < 85 else f"+{df_resultado - 85:.2f}% vs meta"
            )
            
            if mtbf_resultado == float('inf'):
                st.metric("MTBF", "∞ horas", "Sem falhas!")
            else:
                st.metric("MTBF", f"{mtbf_resultado:.2f} h", f"{numero_falhas} falhas")
        
        with col_m2:
            st.metric("MTTR", f"{mttr_resultado:.2f} h", f"{numero_falhas} reparos")
            st.metric("Taxa Preventiva", f"{taxa_preventiva:.1f}%", 
                     f"{taxa_preventiva - 70:.1f}% vs meta 70%" if taxa_preventiva < 70 else "+OK")
        
        # Detalhamento
        st.markdown("**Detalhamento:**")
        dados_detalhe = {
            "Métrica": [
                "Horas Calendário",
                "Horas Operadas",
                "Horas Manutenção Total",
                "  • Preventiva",
                "  • Corretiva",
                "Horas Standby",
                "Número de Falhas"
            ],
            "Valor": [
                f"{horas_calendario:.2f} h",
                f"{horas_operadas:.2f} h",
                f"{horas_manutencao_total:.2f} h",
                f"{horas_preventiva:.2f} h",
                f"{horas_corretiva:.2f} h",
                f"{horas_standby:.2f} h",
                f"{numero_falhas}"
            ]
        }
        st.dataframe(pd.DataFrame(dados_detalhe), hide_index=True, use_container_width=True)
    
    # Gráficos
    st.markdown("---")
    st.subheader("📈 Visualizações")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Gráfico de pizza - Distribuição do tempo
        fig_tempo = go.Figure(data=[go.Pie(
            labels=['Operação', 'Manutenção Preventiva', 'Manutenção Corretiva', 'Standby'],
            values=[horas_operadas, horas_preventiva, horas_corretiva, horas_standby],
            hole=0.4,
            marker_colors=['#2ecc71', '#3498db', '#e74c3c', '#95a5a6']
        )])
        fig_tempo.update_layout(
            title="Distribuição do Tempo",
            height=400
        )
        st.plotly_chart(fig_tempo, use_container_width=True)
    
    with col_g2:
        # Gráfico de indicadores
        fig_kpis = go.Figure()
        
        fig_kpis.add_trace(go.Indicator(
            mode = "gauge+number+delta",
            value = df_resultado,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Disponibilidade Física (%)"},
            delta = {'reference': 85, 'increasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 70], 'color': "lightgray"},
                    {'range': [70, 85], 'color': "yellow"},
                    {'range': [85, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))
        
        fig_kpis.update_layout(height=400)
        st.plotly_chart(fig_kpis, use_container_width=True)
    
    # Análise e recomendações
    st.markdown("---")
    st.subheader("💡 Análise e Recomendações")
    
    recomendacoes = []
    
    if df_resultado < 85:
        recomendacoes.append("⚠️ **DF abaixo da meta (85%)**: Equipamento com baixa disponibilidade. Revise estratégia de manutenção.")
    elif df_resultado > 90:
        recomendacoes.append("✅ **DF excelente**: Equipamento com alta disponibilidade.")
    
    if taxa_preventiva < 70:
        recomendacoes.append(f"⚠️ **Taxa preventiva baixa ({taxa_preventiva:.1f}%)**: Aumente manutenções preventivas para reduzir falhas.")
    elif taxa_preventiva > 80:
        recomendacoes.append(f"✅ **Boa estratégia preventiva ({taxa_preventiva:.1f}%)**: Mantenha o foco em manutenções programadas.")
    
    if mtbf_resultado != float('inf') and mtbf_resultado < 100:
        recomendacoes.append(f"⚠️ **MTBF baixo ({mtbf_resultado:.2f}h)**: Equipamento com muitas falhas. Investigue causas raiz.")
    
    if mttr_resultado > 10:
        recomendacoes.append(f"⚠️ **MTTR alto ({mttr_resultado:.2f}h)**: Reparos demorados. Melhore disponibilidade de peças e capacitação.")
    
    if not recomendacoes:
        recomendacoes.append("✅ **Todos os indicadores dentro da meta**: Continue monitorando e mantenha as boas práticas.")
    
    for rec in recomendacoes:
        st.markdown(rec)

# ========== MODO REVERSO ==========
elif modo_calculo == "🎯 Modo Reverso (Atingir Meta DF)":
    
    st.subheader("🎯 Calculadora Reversa - Atingir Meta de Disponibilidade")
    st.markdown("Calcule **quanto tempo de manutenção** você pode gastar para atingir uma **meta de DF específica**.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Parâmetros de Entrada**")
        
        periodo_rev = st.selectbox(
            "Período de Análise:",
            ["Mês (720h)", "Semana (168h)", "Dia (24h)", "Ano (8760h)", "Personalizado"],
            key="periodo_rev"
        )
        
        if periodo_rev == "Dia (24h)":
            horas_calendario_rev = 24
        elif periodo_rev == "Semana (168h)":
            horas_calendario_rev = 168
        elif periodo_rev == "Mês (720h)":
            horas_calendario_rev = 720
        elif periodo_rev == "Ano (8760h)":
            horas_calendario_rev = 8760
        else:
            horas_calendario_rev = st.number_input("Horas Calendário:", min_value=1.0, value=720.0, key="hc_rev")
        
        df_meta = st.slider(
            "Meta de Disponibilidade Física (DF):",
            min_value=70.0,
            max_value=99.0,
            value=85.0,
            step=0.5,
            format="%.1f%%"
        )
        
        mtbf_alvo = st.number_input(
            "MTBF Alvo (horas):",
            min_value=10.0,
            value=100.0,
            step=10.0,
            help="Tempo médio entre falhas desejado"
        )
        
        mttr_alvo = st.number_input(
            "MTTR Alvo (horas):",
            min_value=0.5,
            value=5.0,
            step=0.5,
            help="Tempo médio de reparo desejado"
        )
        
        taxa_preventiva_alvo = st.slider(
            "Taxa Preventiva Alvo (%):",
            min_value=50.0,
            max_value=90.0,
            value=70.0,
            step=5.0
        )
    
    with col2:
        st.markdown("**Resultados - Tempo Disponível para Manutenção**")
        
        # Cálculo reverso
        # DF = (HC - HM) / HC
        # HM = HC × (1 - DF/100)
        horas_manutencao_max = horas_calendario_rev * (1 - df_meta/100)
        
        # Estimar horas operadas
        horas_operadas_estimadas = horas_calendario_rev - horas_manutencao_max
        
        # Calcular número de falhas esperadas
        numero_falhas_esperadas = horas_operadas_estimadas / mtbf_alvo
        
        # Calcular horas corretivas necessárias
        horas_corretiva_necessarias = numero_falhas_esperadas * mttr_alvo
        
        # Calcular horas preventivas baseadas na taxa alvo
        # Taxa = HP / (HP + HC)
        # HP = HC × Taxa / (1 - Taxa)
        horas_preventiva_necessarias = horas_corretiva_necessarias * (taxa_preventiva_alvo/100) / (1 - taxa_preventiva_alvo/100)
        
        # Total de manutenção calculado
        horas_manutencao_calculada = horas_preventiva_necessarias + horas_corretiva_necessarias
        
        # Ajustar se exceder o máximo
        if horas_manutencao_calculada > horas_manutencao_max:
            fator_ajuste = horas_manutencao_max / horas_manutencao_calculada
            horas_preventiva_necessarias *= fator_ajuste
            horas_corretiva_necessarias *= fator_ajuste
            horas_manutencao_calculada = horas_manutencao_max
        
        # Recalcular DF real
        df_real = calcular_disponibilidade_fisica(horas_calendario_rev, horas_corretiva_necessarias, horas_preventiva_necessarias)
        
        # Exibir resultados
        st.metric("Horas Máximas de Manutenção", f"{horas_manutencao_max:.2f} h")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric("Manutenção Preventiva", f"{horas_preventiva_necessarias:.2f} h")
            st.metric("Número de Falhas Esperadas", f"{numero_falhas_esperadas:.2f}")
        
        with col_r2:
            st.metric("Manutenção Corretiva", f"{horas_corretiva_necessarias:.2f} h")
            st.metric("DF Real Alcançado", f"{df_real:.2f}%")
        
        # Alertas
        if horas_manutencao_calculada > horas_manutencao_max:
            st.warning("⚠️ Os parâmetros de MTBF e MTTR podem não permitir atingir a meta de DF desejada.")
        
        # Resumo em tabela
        st.markdown("**Resumo do Plano:**")
        resumo = {
            "Item": [
                "Horas Calendário",
                "Horas de Operação",
                "Horas Manutenção Total",
                "  • Preventiva",
                "  • Corretiva",
                "Falhas Esperadas",
                "DF Alcançado"
            ],
            "Valor": [
                f"{horas_calendario_rev:.2f} h",
                f"{horas_operadas_estimadas:.2f} h",
                f"{horas_manutencao_calculada:.2f} h",
                f"{horas_preventiva_necessarias:.2f} h",
                f"{horas_corretiva_necessarias:.2f} h",
                f"{numero_falhas_esperadas:.2f}",
                f"{df_real:.2f}%"
            ]
        }
        st.dataframe(pd.DataFrame(resumo), hide_index=True, use_container_width=True)
    
    # Gráfico de comparação
    st.markdown("---")
    st.subheader("📊 Visualização do Plano")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Gráfico de barras comparativo
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name='Disponível',
            x=['Manutenção'],
            y=[horas_manutencao_max],
            marker_color='lightblue'
        ))
        fig_comp.add_trace(go.Bar(
            name='Planejado',
            x=['Manutenção'],
            y=[horas_manutencao_calculada],
            marker_color='darkblue'
        ))
        fig_comp.update_layout(
            title=f"Tempo de Manutenção para DF = {df_meta}%",
            yaxis_title="Horas",
            height=400,
            barmode='group'
        )
        st.plotly_chart(fig_comp, use_container_width=True)
    
    with col_g2:
        # Gráfico de composição
        fig_comp2 = go.Figure(data=[go.Pie(
            labels=['Preventiva', 'Corretiva'],
            values=[horas_preventiva_necessarias, horas_corretiva_necessarias],
            marker_colors=['#3498db', '#e74c3c'],
            hole=0.4
        )])
        fig_comp2.update_layout(
            title="Composição da Manutenção",
            height=400
        )
        st.plotly_chart(fig_comp2, use_container_width=True)

# ========== SIMULAÇÃO E CENÁRIOS ==========
elif modo_calculo == "📈 Simulação e Cenários":
    
    st.subheader("📈 Simulação de Cenários - Análise de Sensibilidade")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Parâmetros Base**")
        
        horas_calendario_sim = st.number_input("Horas Calendário:", min_value=100.0, value=720.0, step=10.0, key="hc_sim")
        horas_preventiva_base = st.number_input("Horas Preventiva Base:", min_value=0.0, value=40.0, step=5.0, key="hp_sim")
        numero_falhas_base = st.number_input("Número Falhas Base:", min_value=1, value=5, step=1, key="nf_sim")
        mttr_base = st.number_input("MTTR Base (h):", min_value=0.5, value=5.0, step=0.5, key="mttr_sim")
        
        st.markdown("**Variação para Simulação**")
        variar = st.selectbox(
            "Variar parâmetro:",
            ["Horas Preventiva", "Número de Falhas", "MTTR", "Horas Preventiva e Falhas"]
        )
    
    with col2:
        st.markdown("**Resultados da Simulação**")
        
        # Criar cenários
        if variar == "Horas Preventiva":
            range_hp = np.linspace(horas_preventiva_base * 0.5, horas_preventiva_base * 1.5, 10)
            resultados = []
            
            for hp in range_hp:
                hc_temp = numero_falhas_base * mttr_base
                df_temp = calcular_disponibilidade_fisica(horas_calendario_sim, hc_temp, hp)
                ho_temp = calcular_horas_operadas(horas_calendario_sim, hp + hc_temp)
                mtbf_temp = calcular_mtbf(ho_temp, numero_falhas_base)
                
                resultados.append({
                    'Horas Preventiva': hp,
                    'DF (%)': df_temp,
                    'MTBF (h)': mtbf_temp if mtbf_temp != float('inf') else 1000,
                    'Horas Operadas': ho_temp
                })
            
            df_sim = pd.DataFrame(resultados)
            
            # Gráfico
            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                x=df_sim['Horas Preventiva'],
                y=df_sim['DF (%)'],
                mode='lines+markers',
                name='DF (%)',
                line=dict(color='blue', width=3)
            ))
            fig_sim.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Meta DF 85%")
            fig_sim.update_layout(
                title="Impacto das Horas Preventivas na Disponibilidade",
                xaxis_title="Horas Preventiva",
                yaxis_title="DF (%)",
                height=400
            )
            st.plotly_chart(fig_sim, use_container_width=True)
            
        elif variar == "Número de Falhas":
            range_falhas = np.arange(1, numero_falhas_base * 2 + 1, 1)
            resultados = []
            
            for nf in range_falhas:
                hc_temp = nf * mttr_base
                df_temp = calcular_disponibilidade_fisica(horas_calendario_sim, hc_temp, horas_preventiva_base)
                ho_temp = calcular_horas_operadas(horas_calendario_sim, horas_preventiva_base + hc_temp)
                mtbf_temp = calcular_mtbf(ho_temp, nf)
                
                resultados.append({
                    'Número de Falhas': nf,
                    'DF (%)': df_temp,
                    'MTBF (h)': mtbf_temp if mtbf_temp != float('inf') else 1000,
                    'MTTR (h)': mttr_base
                })
            
            df_sim = pd.DataFrame(resultados)
            
            # Gráficos duplos
            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                x=df_sim['Número de Falhas'],
                y=df_sim['DF (%)'],
                mode='lines+markers',
                name='DF (%)',
                yaxis='y',
                line=dict(color='blue', width=3)
            ))
            fig_sim.add_trace(go.Scatter(
                x=df_sim['Número de Falhas'],
                y=df_sim['MTBF (h)'],
                mode='lines+markers',
                name='MTBF (h)',
                yaxis='y2',
                line=dict(color='green', width=3)
            ))
            fig_sim.update_layout(
                title="Impacto do Número de Falhas em DF e MTBF",
                xaxis_title="Número de Falhas",
                yaxis=dict(title="DF (%)", side='left'),
                yaxis2=dict(title="MTBF (h)", overlaying='y', side='right'),
                height=400
            )
            st.plotly_chart(fig_sim, use_container_width=True)
            
        elif variar == "MTTR":
            range_mttr = np.linspace(mttr_base * 0.5, mttr_base * 2, 10)
            resultados = []
            
            for mttr_v in range_mttr:
                hc_temp = numero_falhas_base * mttr_v
                df_temp = calcular_disponibilidade_fisica(horas_calendario_sim, hc_temp, horas_preventiva_base)
                ho_temp = calcular_horas_operadas(horas_calendario_sim, horas_preventiva_base + hc_temp)
                
                resultados.append({
                    'MTTR (h)': mttr_v,
                    'DF (%)': df_temp,
                    'Horas Corretiva': hc_temp
                })
            
            df_sim = pd.DataFrame(resultados)
            
            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                x=df_sim['MTTR (h)'],
                y=df_sim['DF (%)'],
                mode='lines+markers',
                name='DF (%)',
                line=dict(color='red', width=3)
            ))
            fig_sim.add_hline(y=85, line_dash="dash", line_color="green", annotation_text="Meta DF 85%")
            fig_sim.update_layout(
                title="Impacto do MTTR na Disponibilidade",
                xaxis_title="MTTR (horas)",
                yaxis_title="DF (%)",
                height=400
            )
            st.plotly_chart(fig_sim, use_container_width=True)
        
        else:  # Horas Preventiva e Falhas
            hp_values = np.linspace(20, 80, 7)
            falhas_values = np.arange(2, 11, 2)
            
            matriz_df = []
            for hp in hp_values:
                linha = []
                for nf in falhas_values:
                    hc_temp = nf * mttr_base
                    df_temp = calcular_disponibilidade_fisica(horas_calendario_sim, hc_temp, hp)
                    linha.append(df_temp)
                matriz_df.append(linha)
            
            fig_sim = go.Figure(data=go.Heatmap(
                z=matriz_df,
                x=falhas_values,
                y=hp_values,
                colorscale='RdYlGn',
                text=[[f"{val:.1f}%" for val in linha] for linha in matriz_df],
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar=dict(title="DF (%)")
            ))
            fig_sim.update_layout(
                title="Mapa de Calor: DF em função de Horas Preventivas e Falhas",
                xaxis_title="Número de Falhas",
                yaxis_title="Horas Preventiva",
                height=500
            )
            st.plotly_chart(fig_sim, use_container_width=True)
        
        # Exibir tabela de dados
        st.markdown("**Dados da Simulação:**")
        st.dataframe(df_sim, use_container_width=True, hide_index=True)

# ========== ANÁLISE HISTÓRICA ==========
else:  # Análise Histórica
    
    st.subheader("📋 Análise Histórica - Múltiplos Períodos")
    st.markdown("Insira dados de vários períodos para análise de tendências.")
    
    # Inicializar session state
    if 'historico_dados' not in st.session_state:
        st.session_state.historico_dados = []
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Adicionar Novo Período**")
        
        with st.form("form_historico"):
            periodo_nome = st.text_input("Nome do Período:", value=f"Mês {len(st.session_state.historico_dados) + 1}")
            hc_hist = st.number_input("Horas Calendário:", min_value=1.0, value=720.0)
            hp_hist = st.number_input("Horas Preventiva:", min_value=0.0, value=40.0)
            nf_hist = st.number_input("Número de Falhas:", min_value=0, value=5)
            hc_mnt_hist = st.number_input("Horas Corretiva:", min_value=0.0, value=30.0)
            
            submitted = st.form_submit_button("➕ Adicionar Período")
            
            if submitted:
                # Calcular KPIs
                ho = calcular_horas_operadas(hc_hist, hp_hist + hc_mnt_hist)
                df_calc = calcular_disponibilidade_fisica(hc_hist, hc_mnt_hist, hp_hist)
                mtbf_calc = calcular_mtbf(ho, nf_hist) if nf_hist > 0 else 0
                mttr_calc = calcular_mttr(hc_mnt_hist, nf_hist) if nf_hist > 0 else 0
                
                novo_registro = {
                    'Período': periodo_nome,
                    'HC': hc_hist,
                    'HP': hp_hist,
                    'Falhas': nf_hist,
                    'HCorretiva': hc_mnt_hist,
                    'HOperadas': ho,
                    'DF': df_calc,
                    'MTBF': mtbf_calc,
                    'MTTR': mttr_calc
                }
                
                st.session_state.historico_dados.append(novo_registro)
                st.success(f"✅ Período '{periodo_nome}' adicionado!")
                st.rerun()
        
        if st.button("🗑️ Limpar Histórico"):
            st.session_state.historico_dados = []
            st.rerun()
    
    with col2:
        if len(st.session_state.historico_dados) > 0:
            st.markdown("**Dados Históricos**")
            
            df_historico = pd.DataFrame(st.session_state.historico_dados)
            
            # Formatar para exibição
            df_display = df_historico.copy()
            df_display['DF'] = df_display['DF'].apply(lambda x: f"{x:.2f}%")
            df_display['MTBF'] = df_display['MTBF'].apply(lambda x: f"{x:.2f}h" if x > 0 else "N/A")
            df_display['MTTR'] = df_display['MTTR'].apply(lambda x: f"{x:.2f}h" if x > 0 else "N/A")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Estatísticas
            st.markdown("**Estatísticas do Período:**")
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            
            with col_s1:
                st.metric("DF Média", f"{df_historico['DF'].mean():.2f}%")
            with col_s2:
                mtbf_validos = df_historico[df_historico['MTBF'] > 0]['MTBF']
                st.metric("MTBF Médio", f"{mtbf_validos.mean():.2f}h" if len(mtbf_validos) > 0 else "N/A")
            with col_s3:
                mttr_validos = df_historico[df_historico['MTTR'] > 0]['MTTR']
                st.metric("MTTR Médio", f"{mttr_validos.mean():.2f}h" if len(mttr_validos) > 0 else "N/A")
            with col_s4:
                st.metric("Total Falhas", f"{df_historico['Falhas'].sum():.0f}")
        else:
            st.info("📝 Nenhum dado histórico. Adicione períodos para ver análises.")
    
    # Gráficos de tendência
    if len(st.session_state.historico_dados) > 1:
        st.markdown("---")
        st.subheader("📊 Análise de Tendências")
        
        df_historico = pd.DataFrame(st.session_state.historico_dados)
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Gráfico de DF ao longo do tempo
            fig_tend_df = go.Figure()
            fig_tend_df.add_trace(go.Scatter(
                x=df_historico['Período'],
                y=df_historico['DF'],
                mode='lines+markers',
                name='DF (%)',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ))
            fig_tend_df.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Meta 85%")
            fig_tend_df.update_layout(
                title="Evolução da Disponibilidade Física",
                xaxis_title="Período",
                yaxis_title="DF (%)",
                height=400
            )
            st.plotly_chart(fig_tend_df, use_container_width=True)
        
        with col_g2:
            # Gráfico de MTBF e MTTR
            fig_tend_mt = go.Figure()
            fig_tend_mt.add_trace(go.Bar(
                x=df_historico['Período'],
                y=df_historico['MTBF'],
                name='MTBF (h)',
                marker_color='lightblue'
            ))
            fig_tend_mt.add_trace(go.Bar(
                x=df_historico['Período'],
                y=df_historico['MTTR'],
                name='MTTR (h)',
                marker_color='lightcoral'
            ))
            fig_tend_mt.update_layout(
                title="MTBF vs MTTR por Período",
                xaxis_title="Período",
                yaxis_title="Horas",
                barmode='group',
                height=400
            )
            st.plotly_chart(fig_tend_mt, use_container_width=True)
        
        # Gráfico de falhas
        fig_falhas = go.Figure()
        fig_falhas.add_trace(go.Bar(
            x=df_historico['Período'],
            y=df_historico['Falhas'],
            marker_color='crimson',
            text=df_historico['Falhas'],
            textposition='outside'
        ))
        fig_falhas.update_layout(
            title="Número de Falhas por Período",
            xaxis_title="Período",
            yaxis_title="Quantidade de Falhas",
            height=400
        )
        st.plotly_chart(fig_falhas, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p><strong>Calculadora de KPIs de Confiabilidade v1.0</strong></p>
        <p>Desenvolvida para gestão de manutenção de frotas de equipamentos móveis</p>
        <p><em>Relações matemáticas: DF, MTBF, MTTR e Horas de Manutenção</em></p>
    </div>
""", unsafe_allow_html=True)
