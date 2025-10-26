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

# CSS personalizado com alto contraste
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    /* Melhorar contraste dos cards de métricas */
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        border: 2px solid #e0e0e0;
    }
    .stMetric label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #0066cc !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    /* Cards customizados */
    .kpi-card {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    h1 {
        color: #1565C0;
    }
    h2, h3 {
        color: #1a1a1a;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f5f5f5;
    }
    /* Melhorar contraste de dataframes */
    .stDataFrame {
        background-color: white;
    }
    /* Botões com melhor contraste */
    .stButton button {
        background-color: #1976D2;
        color: white;
        font-weight: 600;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
    }
    .stButton button:hover {
        background-color: #1565C0;
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
     "📐 Escala MTBF/MTTR vs DF",
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
        
        # Meta de DF editável
        st.markdown("**🎯 Metas de Referência**")
        meta_df = st.number_input(
            "Meta de DF (%):",
            min_value=70.0,
            max_value=99.0,
            value=85.0,
            step=0.5,
            help="Defina sua meta de disponibilidade"
        )
        
        meta_preventiva = st.number_input(
            "Meta Taxa Preventiva (%):",
            min_value=20.0,
            max_value=90.0,
            value=35.0,
            step=1.0,
            help="Meta de % preventiva sobre total de manutenção"
        )
        
        st.markdown("---")
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
            delta_df = df_resultado - meta_df
            st.metric(
                "Disponibilidade Física (DF)", 
                f"{df_resultado:.2f}%",
                delta=f"{delta_df:.2f}% vs meta {meta_df:.1f}%"
            )
            
            if numero_falhas == 0:
                st.metric("MTBF", "∞ horas", "Sem falhas!")
            elif mtbf_resultado == float('inf') or mtbf_resultado == 0:
                st.metric("MTBF", "0.00 h", "Sem operação")
            else:
                st.metric("MTBF", f"{mtbf_resultado:.2f} h", f"{numero_falhas} falhas")
        
        with col_m2:
            if numero_falhas == 0:
                st.metric("MTTR", "0.00 h", "Sem falhas")
            else:
                st.metric("MTTR", f"{mttr_resultado:.2f} h", f"{numero_falhas} reparos")
            delta_prev = taxa_preventiva - meta_preventiva
            st.metric("Taxa Preventiva", f"{taxa_preventiva:.1f}%", 
                     f"{delta_prev:.1f}% vs meta {meta_preventiva:.1f}%")
        
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
        # Gráfico de pizza MELHORADO - Distribuição do tempo
        # Garantir que valores são numéricos válidos
        valores_pizza = [
            float(horas_operadas) if horas_operadas is not None else 0.0,
            float(horas_preventiva) if horas_preventiva is not None else 0.0,
            float(horas_corretiva) if horas_corretiva is not None else 0.0,
            float(horas_standby) if horas_standby is not None else 0.0
        ]
        
        fig_tempo = go.Figure(data=[go.Pie(
            labels=['Operação', 'Manutenção Preventiva', 'Manutenção Corretiva', 'Standby'],
            values=valores_pizza,
            hole=0.5,
            marker=dict(
                colors=['#27AE60', '#3498DB', '#E74C3C', '#95A5A6'],
                line=dict(color='white', width=3)
            ),
            textposition='outside',
            textfont=dict(size=14, color='#1a1a1a', family='Arial Black'),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br><b>%{value:.1f} horas</b><br>%{percent}<extra></extra>',
            pull=[0.05, 0, 0, 0]  # Destaca operação
        )])
        
        # Anotação central
        fig_tempo.add_annotation(
            text=f"<b>{horas_calendario:.0f}h</b><br>Total",
            x=0.5, y=0.5,
            font=dict(size=20, color='#1565C0', family='Arial Black'),
            showarrow=False
        )
        
        fig_tempo.update_layout(
            title=dict(
                text="<b>Distribuição do Tempo</b>",
                font=dict(size=20, color='#1a1a1a', family='Arial Black'),
                x=0.5,
                xanchor='center'
            ),
            height=450,
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(size=13, family='Arial'),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05,
                font=dict(size=12)
            )
        )
        st.plotly_chart(fig_tempo, use_container_width=True)
    
    with col_g2:
        # Gráfico de indicadores
        fig_kpis = go.Figure()
        
        # Garantir valores válidos
        df_resultado_safe = float(df_resultado) if df_resultado is not None else 0.0
        meta_df_safe = float(meta_df) if meta_df is not None else 85.0
        
        # Determinar cor baseada na meta
        if df_resultado_safe >= meta_df_safe:
            cor_gauge = "#27AE60"  # Verde
        elif df_resultado_safe >= meta_df_safe - 5:
            cor_gauge = "#F39C12"  # Laranja
        else:
            cor_gauge = "#E74C3C"  # Vermelho
        
        fig_kpis.add_trace(go.Indicator(
            mode = "gauge+number+delta",
            value = df_resultado_safe,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {
                'text': f"<b>Disponibilidade Física</b><br><span style='font-size:14px'>Meta: {meta_df_safe:.1f}%</span>",
                'font': {'size': 20, 'color': '#1a1a1a', 'family': 'Arial Black'}
            },
            delta = {
                'reference': meta_df_safe,
                'increasing': {'color': "#27AE60"},
                'decreasing': {'color': "#E74C3C"},
                'font': {'size': 16}
            },
            number = {'font': {'size': 56, 'color': cor_gauge, 'family': 'Arial Black'}, 'suffix': '%'},
            gauge = {
                'axis': {
                    'range': [None, 100],
                    'tickwidth': 3,
                    'tickcolor': "#1a1a1a",
                    'tickfont': {'size': 14, 'family': 'Arial'}
                },
                'bar': {'color': cor_gauge, 'thickness': 0.75},
                'bgcolor': "white",
                'borderwidth': 3,
                'bordercolor': "#E0E0E0",
                'steps': [
                    {'range': [0, max(0, meta_df_safe - 10)], 'color': "#FFCDD2"},
                    {'range': [max(0, meta_df_safe - 10), meta_df_safe], 'color': "#FFF9C4"},
                    {'range': [meta_df_safe, 100], 'color': "#C8E6C9"}
                ],
                'threshold': {
                    'line': {'color': "#1565C0", 'width': 5},
                    'thickness': 0.8,
                    'value': meta_df_safe
                }
            }
        ))
        
        fig_kpis.update_layout(
            height=450,
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(size=14, color='#1a1a1a', family='Arial'),
            margin=dict(l=20, r=20, t=80, b=20)
        )
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
        
        df_meta = st.number_input(
            "Meta de Disponibilidade Física (DF %):",
            min_value=70.0,
            max_value=99.0,
            value=85.0,
            step=0.5,
            format="%.1f",
            help="Defina sua meta de disponibilidade desejada"
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
        
        taxa_preventiva_alvo = st.number_input(
            "Taxa Preventiva Alvo (%):",
            min_value=20.0,
            max_value=90.0,
            value=35.0,
            step=1.0,
            format="%.1f",
            help="Percentual de manutenção preventiva sobre o total de manutenção"
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
        # Gráfico de barras MELHORADO
        fig_comp = go.Figure()
        
        # Calcular percentual usado
        percentual_usado = (horas_manutencao_calculada / horas_manutencao_max) * 100
        
        fig_comp.add_trace(go.Bar(
            name=f'Disponível ({horas_manutencao_max:.1f}h)',
            x=['Manutenção Total'],
            y=[horas_manutencao_max],
            marker=dict(
                color='#E8F5E9',
                line=dict(color='#4CAF50', width=3)
            ),
            text=[f"{horas_manutencao_max:.1f}h<br>(100%)"],
            textposition='inside',
            textfont=dict(size=16, color='#2E7D32', family='Arial Black'),
            width=0.6
        ))
        
        fig_comp.add_trace(go.Bar(
            name=f'Planejado ({horas_manutencao_calculada:.1f}h)',
            x=['Manutenção Total'],
            y=[horas_manutencao_calculada],
            marker=dict(
                color='#1976D2',
                line=dict(color='#0D47A1', width=2)
            ),
            text=[f"{horas_manutencao_calculada:.1f}h<br>({percentual_usado:.1f}%)"],
            textposition='inside',
            textfont=dict(size=16, color='white', family='Arial Black'),
            width=0.6
        ))
        
        fig_comp.update_layout(
            title=dict(
                text=f"<b>Tempo de Manutenção para DF = {df_meta:.1f}%</b>",
                font=dict(size=20, color='#1a1a1a', family='Arial Black'),
                x=0.5,
                xanchor='center'
            ),
            yaxis=dict(
                title="<b>Horas</b>",
                titlefont=dict(size=16, family='Arial Black'),
                tickfont=dict(size=14),
                gridcolor='#E0E0E0',
                gridwidth=1
            ),
            xaxis=dict(
                tickfont=dict(size=16, family='Arial Black')
            ),
            height=450,
            barmode='overlay',
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(size=13, color='#1a1a1a', family='Arial'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            ),
            margin=dict(t=100)
        )
        st.plotly_chart(fig_comp, use_container_width=True)
    
    with col_g2:
        # Gráfico de pizza MELHORADO - Composição
        taxa_preventiva_real = (horas_preventiva_necessarias / horas_manutencao_calculada) * 100 if horas_manutencao_calculada > 0 else 0
        
        fig_comp2 = go.Figure(data=[go.Pie(
            labels=[f'Preventiva ({taxa_preventiva_real:.1f}%)', f'Corretiva ({100-taxa_preventiva_real:.1f}%)'],
            values=[horas_preventiva_necessarias, horas_corretiva_necessarias],
            marker=dict(
                colors=['#3498DB', '#E74C3C'],
                line=dict(color='white', width=4)
            ),
            hole=0.5,
            textposition='outside',
            textfont=dict(size=14, color='#1a1a1a', family='Arial Black'),
            textinfo='label+value',
            hovertemplate='<b>%{label}</b><br><b>%{value:.1f} horas</b><extra></extra>',
            pull=[0.05, 0.05]
        )])
        
        # Anotação central
        fig_comp2.add_annotation(
            text=f"<b>{horas_manutencao_calculada:.1f}h</b><br>Total",
            x=0.5, y=0.5,
            font=dict(size=20, color='#1565C0', family='Arial Black'),
            showarrow=False
        )
        
        fig_comp2.update_layout(
            title=dict(
                text="<b>Composição da Manutenção</b>",
                font=dict(size=20, color='#1a1a1a', family='Arial Black'),
                x=0.5,
                xanchor='center'
            ),
            height=450,
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(size=13, family='Arial'),
            showlegend=False,
            margin=dict(t=60)
        )
        st.plotly_chart(fig_comp2, use_container_width=True)

# ========== SIMULAÇÃO E CENÁRIOS ==========
elif modo_calculo == "📈 Simulação e Cenários":
    
    st.subheader("📈 Simulação de Cenários - Análise de Sensibilidade")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**🎯 Meta de Referência**")
        meta_df_sim = st.number_input(
            "Meta de DF (%):",
            min_value=70.0,
            max_value=99.0,
            value=85.0,
            step=0.5,
            key="meta_df_sim",
            help="Linha de referência no gráfico"
        )
        
        st.markdown("---")
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
            
            # Gráfico MELHORADO
            fig_sim = go.Figure()
            
            # Linha principal
            fig_sim.add_trace(go.Scatter(
                x=df_sim['Horas Preventiva'],
                y=df_sim['DF (%)'],
                mode='lines+markers',
                name='DF (%)',
                line=dict(color='#1976D2', width=4),
                marker=dict(
                    size=10,
                    color='#1976D2',
                    line=dict(color='white', width=2)
                ),
                hovertemplate='<b>Horas Preventiva:</b> %{x:.1f}h<br><b>DF:</b> %{y:.2f}%<extra></extra>'
            ))
            
            # Linha de meta
            fig_sim.add_hline(
                y=meta_df_sim,
                line_dash="dash",
                line_color="#E74C3C",
                line_width=3,
                annotation_text=f"Meta DF {meta_df_sim:.1f}%",
                annotation_position="right",
                annotation=dict(
                    font=dict(size=14, color='#E74C3C', family='Arial Black'),
                    bgcolor='white',
                    bordercolor='#E74C3C',
                    borderwidth=2
                )
            )
            
            # Área sob/sobre a meta
            fig_sim.add_hrect(
                y0=0, y1=meta_df_sim,
                fillcolor="red", opacity=0.1,
                layer="below", line_width=0
            )
            fig_sim.add_hrect(
                y0=meta_df_sim, y1=100,
                fillcolor="green", opacity=0.1,
                layer="below", line_width=0
            )
            
            fig_sim.update_layout(
                title=dict(
                    text="<b>Impacto das Horas Preventivas na Disponibilidade</b>",
                    font=dict(size=20, color='#1a1a1a', family='Arial Black'),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis=dict(
                    title="<b>Horas Preventiva</b>",
                    titlefont=dict(size=16, family='Arial Black'),
                    tickfont=dict(size=14),
                    gridcolor='#E0E0E0',
                    gridwidth=1,
                    showline=True,
                    linewidth=2,
                    linecolor='#1a1a1a'
                ),
                yaxis=dict(
                    title="<b>Disponibilidade Física (%)</b>",
                    titlefont=dict(size=16, family='Arial Black'),
                    tickfont=dict(size=14),
                    gridcolor='#E0E0E0',
                    gridwidth=1,
                    showline=True,
                    linewidth=2,
                    linecolor='#1a1a1a',
                    range=[70, 100]
                ),
                height=500,
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(size=13, family='Arial'),
                hovermode='x unified',
                showlegend=False
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
                height=500,
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(size=13, color='#1a1a1a')
            )
            st.plotly_chart(fig_sim, use_container_width=True)
            
            # Criar dataframe para este cenário
            dados_heatmap = []
            for i, hp in enumerate(hp_values):
                for j, nf in enumerate(falhas_values):
                    dados_heatmap.append({
                        'Horas Preventiva': hp,
                        'Número Falhas': nf,
                        'DF (%)': matriz_df[i][j]
                    })
            df_sim = pd.DataFrame(dados_heatmap)
        
        # Exibir tabela de dados
        st.markdown("**Dados da Simulação:**")
        if len(df_sim) > 20:
            st.dataframe(df_sim.head(20), use_container_width=True, hide_index=True)
            st.info(f"📊 Mostrando primeiras 20 linhas de {len(df_sim)} total")
        else:
            st.dataframe(df_sim, use_container_width=True, hide_index=True)

# ========== ESCALA MTBF/MTTR vs DF ==========
elif modo_calculo == "📐 Escala MTBF/MTTR vs DF":
    
    st.subheader("📐 Escala de Referência: Relação MTBF/MTTR com Disponibilidade Física")
    st.markdown("Entenda como diferentes combinações de **MTBF** e **MTTR** impactam a **Disponibilidade Física (DF)**.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**⚙️ Parâmetros de Simulação**")
        
        horas_calendario_escala = st.number_input(
            "Horas Calendário (período):",
            min_value=100.0,
            value=720.0,
            step=10.0,
            help="Período de análise (ex: 720h = 1 mês)"
        )
        
        horas_preventiva_escala = st.number_input(
            "Horas Preventiva (fixo):",
            min_value=0.0,
            value=50.0,
            step=5.0,
            help="Horas de manutenção preventiva no período"
        )
        
        st.markdown("**🔹 Faixas de Simulação**")
        
        mtbf_min = st.number_input("MTBF Mínimo (h):", min_value=10.0, value=30.0, step=5.0)
        mtbf_max = st.number_input("MTBF Máximo (h):", min_value=mtbf_min + 10, value=200.0, step=10.0)
        
        mttr_min = st.number_input("MTTR Mínimo (h):", min_value=0.5, value=2.0, step=0.5)
        mttr_max = st.number_input("MTTR Máximo (h):", min_value=mttr_min + 0.5, value=12.0, step=0.5)
        
        st.info("💡 **Dica:** Ajuste as faixas para focar na realidade da sua operação")
    
    with col2:
        st.markdown("**🎯 Mapa de Calor: MTBF vs MTTR → Disponibilidade Física**")
        
        # Criar grades de valores
        mtbf_values = np.linspace(mtbf_min, mtbf_max, 8)
        mttr_values = np.linspace(mttr_min, mttr_max, 8)
        
        # Matriz para armazenar DF
        matriz_df_escala = []
        
        for mttr_val in mttr_values:
            linha = []
            for mtbf_val in mtbf_values:
                # Calcular horas operadas (aproximado)
                horas_disponiveis = horas_calendario_escala - horas_preventiva_escala
                
                # Estimar número de falhas baseado no MTBF
                numero_falhas_est = horas_disponiveis / mtbf_val
                
                # Calcular horas corretivas baseado no MTTR
                horas_corretiva_est = numero_falhas_est * mttr_val
                
                # Calcular DF
                df_calculado = calcular_disponibilidade_fisica(
                    horas_calendario_escala, 
                    horas_corretiva_est, 
                    horas_preventiva_escala
                )
                
                linha.append(df_calculado)
            matriz_df_escala.append(linha)
        
        # Criar heatmap
        fig_escala = go.Figure(data=go.Heatmap(
            z=matriz_df_escala,
            x=[f"{val:.0f}h" for val in mtbf_values],
            y=[f"{val:.1f}h" for val in mttr_values],
            colorscale='RdYlGn',
            text=[[f"{val:.1f}%" for val in linha] for linha in matriz_df_escala],
            texttemplate="%{text}",
            textfont={"size": 11, "color": "black"},
            colorbar=dict(
                title="DF (%)",
                tickmode="linear",
                tick0=70,
                dtick=5
            ),
            hovertemplate='<b>MTBF:</b> %{x}<br><b>MTTR:</b> %{y}<br><b>DF:</b> %{text}<extra></extra>'
        ))
        
        fig_escala.update_layout(
            title=dict(
                text="Disponibilidade Física (DF) em função de MTBF e MTTR",
                font=dict(size=16, color='#1a1a1a')
            ),
            xaxis_title="MTBF (Tempo Médio Entre Falhas)",
            yaxis_title="MTTR (Tempo Médio de Reparo)",
            height=500,
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(size=12, color='#1a1a1a')
        )
        
        st.plotly_chart(fig_escala, use_container_width=True)
    
    # Interpretação e guia
    st.markdown("---")
    st.subheader("📊 Interpretação da Escala")
    
    col_i1, col_i2 = st.columns(2)
    
    with col_i1:
        st.markdown("""
        **🔴 Zona Vermelha (DF < 80%)**
        - **MTBF baixo** E/OU **MTTR alto**
        - Equipamento pouco confiável
        - Falhas frequentes e/ou reparos demorados
        - **Ação urgente necessária**
        
        **🟡 Zona Amarela (DF 80-85%)**
        - **MTBF moderado** com **MTTR razoável**
        - Operação aceitável mas pode melhorar
        - **Monitoramento contínuo**
        
        **🟢 Zona Verde (DF > 85%)**
        - **MTBF alto** E **MTTR baixo**
        - Equipamento confiável e reparos rápidos
        - **Operação world-class**
        """)
    
    with col_i2:
        st.markdown("""
        **🎯 Estratégias para Melhorar DF:**
        
        **1. Aumentar MTBF (→):**
        - Manutenção preventiva eficaz
        - Análise de causa raiz de falhas
        - Substituição de componentes críticos
        - Manutenção preditiva (sensores, vibração)
        - Treinamento de operadores
        
        **2. Reduzir MTTR (↓):**
        - Disponibilidade de peças no local
        - Ferramentas adequadas
        - Capacitação da equipe
        - Procedimentos padronizados
        - Suporte técnico rápido
        
        **3. Combinação Ideal:**
        - **MTBF > 100h** + **MTTR < 5h** = **DF > 90%** ✅
        """)
    
    # Tabela de referência
    st.markdown("---")
    st.subheader("📊 Tabela de Referência Rápida")
    
    # Criar alguns pontos de referência
    referencias = []
    cenarios = [
        {"Cenário": "Crítico", "MTBF": 30, "MTTR": 10},
        {"Cenário": "Ruim", "MTBF": 50, "MTTR": 8},
        {"Cenário": "Aceitável", "MTBF": 80, "MTTR": 6},
        {"Cenário": "Bom", "MTBF": 120, "MTTR": 5},
        {"Cenário": "Excelente", "MTBF": 150, "MTTR": 4},
        {"Cenário": "World-Class", "MTBF": 200, "MTTR": 3}
    ]
    
    for cenario in cenarios:
        horas_disponiveis_ref = horas_calendario_escala - horas_preventiva_escala
        falhas_ref = horas_disponiveis_ref / cenario["MTBF"]
        horas_corr_ref = falhas_ref * cenario["MTTR"]
        df_ref = calcular_disponibilidade_fisica(horas_calendario_escala, horas_corr_ref, horas_preventiva_escala)
        
        # Classificação
        if df_ref >= 90:
            classe = "🟢 Excelente"
        elif df_ref >= 85:
            classe = "🟢 Bom"
        elif df_ref >= 80:
            classe = "🟡 Aceitável"
        else:
            classe = "🔴 Crítico"
        
        referencias.append({
            "Cenário": cenario["Cenário"],
            "MTBF (h)": cenario["MTBF"],
            "MTTR (h)": cenario["MTTR"],
            "Falhas Estimadas": f"{falhas_ref:.1f}",
            "DF (%)": f"{df_ref:.2f}%",
            "Classificação": classe
        })
    
    df_referencias = pd.DataFrame(referencias)
    st.dataframe(df_referencias, use_container_width=True, hide_index=True)
    
    st.success("🎯 **Objetivo:** Mover seu equipamento para cima na tabela, aumentando MTBF e reduzindo MTTR!")

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
            
            # Estatísticas com melhor visualização
            st.markdown("**📊 Estatísticas do Período:**")
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            
            df_media = df_historico['DF'].mean()
            with col_s1:
                st.metric(
                    "DF Média", 
                    f"{df_media:.2f}%",
                    delta=f"{df_media - 85:.1f}% vs 85%" if df_media < 85 else f"+{df_media - 85:.1f}%"
                )
            with col_s2:
                mtbf_validos = df_historico[df_historico['MTBF'] > 0]['MTBF']
                if len(mtbf_validos) > 0:
                    st.metric("MTBF Médio", f"{mtbf_validos.mean():.2f}h", delta=f"{len(mtbf_validos)} períodos")
                else:
                    st.metric("MTBF Médio", "N/A")
            with col_s3:
                mttr_validos = df_historico[df_historico['MTTR'] > 0]['MTTR']
                if len(mttr_validos) > 0:
                    st.metric("MTTR Médio", f"{mttr_validos.mean():.2f}h", delta=f"{len(mttr_validos)} períodos")
                else:
                    st.metric("MTTR Médio", "N/A")
            with col_s4:
                st.metric(
                    "Total Falhas", 
                    f"{df_historico['Falhas'].sum():.0f}",
                    delta=f"{df_historico['Falhas'].mean():.1f} falhas/período"
                )
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
