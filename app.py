import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import scipy.stats as stats
from scipy.optimize import minimize_scalar, curve_fit
from scipy.interpolate import interp1d
import io

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
     "📉 Curva Característica de Manutenção",
     "📚 Análise Histórica"],
    index=0
)

# Método de cálculo da DF
st.sidebar.markdown("---")
st.sidebar.subheader("Método de Cálculo da DF:")
metodo_df = st.sidebar.radio(
    "Escolha o método:",
    ["Método 1: DF Total (inclui preventiva)",
     "Método 2: DF por MTBF/MTTR (exclui preventiva)"],
    index=0,
    help="""
    Método 1: DF = (Horas Operadas / Horas Calendário) × 100
    - Considera todas as paradas (preventiva + corretiva)
    
    Método 2: DF = MTBF / (MTBF + MTTR) × 100
    - Considera apenas paradas corretivas (falhas)
    - Exclui manutenção preventiva programada
    """
)

# Relações entre KPIs
st.sidebar.markdown("---")
st.sidebar.subheader("Relações entre KPIs:")

if "Método 1" in metodo_df:
    st.sidebar.markdown("""
    **Método 1 (DF Total):**
    • DF = (Horas Operadas / Horas Calendário) × 100
    • Horas Operadas = Calendário - Preventiva - Corretiva
    • MTBF = Horas Operadas / Número de Falhas
    • MTTR = Horas Corretivas / Número de Falhas
    """)
else:
    st.sidebar.markdown("""
    **Método 2 (DF por MTBF/MTTR):**
    • DF = MTBF / (MTBF + MTTR) × 100
    • Horas Disponíveis = Calendário - Preventiva
    • MTBF = Horas Disponíveis / Número de Falhas
    • MTTR = Horas Corretivas / Número de Falhas
    • Exclui preventiva do cálculo de DF
    """)

# Função para calcular KPIs
def calcular_kpis(horas_calendario, horas_preventiva, horas_corretiva, num_falhas, metodo="metodo1"):
    """
    Calcula os KPIs operacionais
    
    Método 1: DF Total (inclui preventiva)
    Método 2: DF por MTBF/MTTR (exclui preventiva)
    """
    
    # Horas totais de manutenção
    horas_manutencao_total = horas_preventiva + horas_corretiva
    
    if metodo == "metodo1":
        # MÉTODO 1: DF Total (inclui preventiva)
        # Horas operadas considerando TODAS as paradas
        horas_operadas = horas_calendario - horas_manutencao_total
        
        # Disponibilidade Física Total
        df = (horas_operadas / horas_calendario * 100) if horas_calendario > 0 else 0
        
        # MTBF baseado nas horas operadas
        mtbf = horas_operadas / num_falhas if num_falhas > 0 else 0
        
    else:
        # MÉTODO 2: DF por MTBF/MTTR (exclui preventiva)
        # Horas disponíveis para operação (exclui apenas preventiva)
        horas_disponiveis = horas_calendario - horas_preventiva
        
        # Horas efetivamente operadas (disponíveis - corretiva)
        horas_operadas = horas_disponiveis - horas_corretiva
        
        # MTBF baseado nas horas disponíveis (sem preventiva)
        mtbf = horas_disponiveis / num_falhas if num_falhas > 0 else 0
        
        # DF calculada pela fórmula clássica: MTBF / (MTBF + MTTR)
        mttr_temp = horas_corretiva / num_falhas if num_falhas > 0 else 0
        df = (mtbf / (mtbf + mttr_temp) * 100) if (mtbf + mttr_temp) > 0 else 0
    
    # MTTR (igual em ambos os métodos)
    mttr = horas_corretiva / num_falhas if num_falhas > 0 else 0
    
    # Horas standby
    horas_standby = max(0, horas_calendario - horas_operadas - horas_manutencao_total)
    
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
        'horas_calendario': horas_calendario,
        'horas_disponiveis': horas_calendario - horas_preventiva if metodo == "metodo2" else horas_calendario
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

# Funções para Curva Característica
def calcular_ponto_otimo_intervencao(df_curva, df_alvo=85, custo_preventiva=1000, custo_corretiva=5000):
    """
    Calcula o ponto ótimo para intervenção baseado em DF alvo e custos
    """
    
    # Calcular DF para cada ponto
    df_curva['df_calculada'] = (df_curva['mtbf_observado'] / 
                                 (df_curva['mtbf_observado'] + df_curva['mttr_observado']) * 100)
    
    # Encontrar ponto onde DF atinge o alvo
    df_acima_alvo = df_curva[df_curva['df_calculada'] >= df_alvo]
    
    if len(df_acima_alvo) > 0:
        tempo_max_alvo = df_acima_alvo['tempo_desde_preventiva_horas'].max()
    else:
        tempo_max_alvo = 0
    
    # Calcular custo total para diferentes intervalos
    custos = []
    for _, row in df_curva.iterrows():
        tempo = row['tempo_desde_preventiva_horas']
        num_falhas_acum = df_curva[df_curva['tempo_desde_preventiva_horas'] <= tempo]['num_falhas'].sum()
        
        # Custo total = preventiva + corretivas
        custo_total = custo_preventiva + (num_falhas_acum * custo_corretiva)
        custo_por_hora = custo_total / tempo if tempo > 0 else 0
        
        custos.append({
            'tempo': tempo,
            'custo_total': custo_total,
            'custo_por_hora': custo_por_hora,
            'df': row['df_calculada']
        })
    
    df_custos = pd.DataFrame(custos)
    
    # Ponto ótimo: menor custo por hora mantendo DF aceitável
    df_custos_viavel = df_custos[df_custos['df'] >= df_alvo * 0.95]  # 95% do alvo
    
    if len(df_custos_viavel) > 0:
        idx_otimo = df_custos_viavel['custo_por_hora'].idxmin()
        ponto_otimo = df_custos_viavel.loc[idx_otimo]
    else:
        idx_otimo = df_custos['custo_por_hora'].idxmin()
        ponto_otimo = df_custos.loc[idx_otimo]
    
    return {
        'tempo_otimo': ponto_otimo['tempo'],
        'df_no_ponto_otimo': ponto_otimo['df'],
        'custo_por_hora_otimo': ponto_otimo['custo_por_hora'],
        'tempo_max_alvo': tempo_max_alvo,
        'df_custos': df_custos
    }

def ajustar_curva_degradacao(df_curva):
    """
    Ajusta uma curva de degradação aos dados observados
    """
    x = df_curva['tempo_desde_preventiva_horas'].values
    y = df_curva['mtbf_observado'].values
    
    # Tentar ajuste exponencial: y = a * exp(-b * x) + c
    def func_exp(x, a, b, c):
        return a * np.exp(-b * x) + c
    
    try:
        popt, _ = curve_fit(func_exp, x, y, p0=[y[0], 0.001, y[-1]], maxfev=10000)
        
        # Gerar pontos da curva ajustada
        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = func_exp(x_fit, *popt)
        
        return x_fit, y_fit, popt
    except:
        # Se falhar, retornar interpolação linear
        f = interp1d(x, y, kind='linear', fill_value='extrapolate')
        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = f(x_fit)
        return x_fit, y_fit, None

def gerar_template_curva_caracteristica():
    """
    Gera template Excel para download
    """
    # Dados de exemplo
    data_preventiva = datetime(2024, 1, 15)
    
    dados_exemplo = []
    
    for semana in range(1, 21):
        data_periodo = data_preventiva + timedelta(weeks=semana)
        horas_operadas = 160
        
        # MTBF degrada ao longo do tempo
        mtbf_inicial = 200
        mtbf_minimo = 40
        mtbf = mtbf_minimo + (mtbf_inicial - mtbf_minimo) * (0.95 ** semana)
        
        num_falhas = max(1, int(horas_operadas / mtbf))
        mttr_base = 4
        mttr = mttr_base + (semana * 0.15)
        horas_corretiva = num_falhas * mttr
        tempo_desde_preventiva = semana * 168
        
        dados_exemplo.append({
            'data_periodo': data_periodo.strftime('%Y-%m-%d'),
            'semana_apos_preventiva': semana,
            'tempo_desde_preventiva_horas': tempo_desde_preventiva,
            'horas_operadas': round(horas_operadas, 2),
            'num_falhas': num_falhas,
            'horas_corretiva': round(horas_corretiva, 2),
            'mtbf_observado': round(mtbf, 2),
            'mttr_observado': round(mttr, 2),
            'observacoes': ''
        })
    
    dados_exemplo[0]['observacoes'] = 'Logo após preventiva - equipamento em condição ótima'
    dados_exemplo[9]['observacoes'] = 'Início da degradação acelerada'
    dados_exemplo[14]['observacoes'] = 'Ponto crítico - considerar intervenção'
    dados_exemplo[19]['observacoes'] = 'Degradação severa - intervenção urgente'
    
    df_exemplo = pd.DataFrame(dados_exemplo)
    
    # Criar arquivo Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Template vazio
        df_template = pd.DataFrame({
            'data_periodo': ['2024-01-22', '2024-01-29', '...'],
            'semana_apos_preventiva': [1, 2, '...'],
            'tempo_desde_preventiva_horas': [168, 336, '...'],
            'horas_operadas': [160, 155, '...'],
            'num_falhas': [1, 2, '...'],
            'horas_corretiva': [4, 10, '...'],
            'mtbf_observado': [160, 77.5, '...'],
            'mttr_observado': [4, 5, '...'],
            'observacoes': ['', '', '']
        })
        df_template.to_excel(writer, sheet_name='Template_Vazio', index=False)
        
        # Exemplo preenchido
        df_exemplo.to_excel(writer, sheet_name='Exemplo_Preenchido', index=False)
        
        # Instruções
        instrucoes = pd.DataFrame({
            'INSTRUÇÕES': [
                'CURVA CARACTERÍSTICA DE MANUTENÇÃO',
                '',
                '1. Use a aba "Template_Vazio" como base',
                '2. Preencha os dados após cada preventiva',
                '3. Colete dados por pelo menos 10-20 períodos',
                '',
                'COLUNAS OBRIGATÓRIAS:',
                '• data_periodo: Data do período (YYYY-MM-DD)',
                '• semana_apos_preventiva: Semana após preventiva',
                '• tempo_desde_preventiva_horas: Horas acumuladas',
                '• horas_operadas: Horas operadas no período',
                '• num_falhas: Número de falhas',
                '• horas_corretiva: Horas em reparo',
                '• mtbf_observado: MTBF calculado',
                '• mttr_observado: MTTR calculado',
                '',
                'O sistema calculará automaticamente:',
                '• Curva de degradação',
                '• Ponto ótimo de intervenção',
                '• DF projetada',
                '• Análise de custos'
            ]
        })
        instrucoes.to_excel(writer, sheet_name='Instrucoes', index=False, header=False)
    
    output.seek(0)
    return output

# Determinar método de cálculo
metodo_atual = "metodo1" if "Método 1" in metodo_df else "metodo2"

# MODO 1: Modo Direto (Calcular KPIs)
if "Modo Direto" in modo_calculo:
    st.header("📊 Dados de Entrada")
    
    # Explicação do método selecionado
    if metodo_atual == "metodo1":
        st.info("""
        **Método 1 - DF Total (inclui preventiva)**
        
        Neste método, a Disponibilidade Física considera TODAS as paradas de manutenção:
        - DF = (Horas Operadas / Horas Calendário) × 100
        - Horas Operadas = Calendário - Preventiva - Corretiva
        """)
    else:
        st.info("""
        **Método 2 - DF por MTBF/MTTR (exclui preventiva)**
        
        Neste método, a Disponibilidade Física usa a fórmula clássica:
        - DF = MTBF / (MTBF + MTTR) × 100
        - MTBF é calculado sobre horas disponíveis (Calendário - Preventiva)
        - Considera apenas falhas não programadas
        """)
    
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
            help="Total de horas em manutenção preventiva programada"
        )
    
    with col2:
        num_falhas = st.number_input(
            "Número de Falhas/Quebras:",
            min_value=0,
            value=5,
            step=1,
            help="Quantidade de falhas ou quebras não programadas no período"
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
    kpis = calcular_kpis(horas_calendario, horas_preventiva, horas_corretiva, num_falhas, metodo_atual)
    
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
        if metodo_atual == "metodo2":
            st.caption("📌 Calculado por MTBF/(MTBF+MTTR)")
        else:
            st.caption("📌 Inclui todas as paradas")
    
    with col2:
        st.metric(
            "MTTR",
            f"{kpis['mttr']:.2f} h",
            f"⚠ {num_falhas} reparos" if num_falhas > 0 else "✓ Sem falhas"
        )
        st.caption("📌 Tempo médio de reparo")
    
    with col3:
        st.metric(
            "MTBF",
            f"{kpis['mtbf']:.2f} h",
            f"↑ {num_falhas} falhas" if num_falhas > 0 else "✓ Sem falhas"
        )
        if metodo_atual == "metodo2":
            st.caption("📌 Baseado em horas disponíveis")
        else:
            st.caption("📌 Baseado em horas operadas")
    
    with col4:
        st.metric(
            "Taxa Preventiva",
            f"{kpis['taxa_preventiva']:.2f}%",
            f"{kpis['taxa_preventiva'] - meta_preventiva:+.2f}% vs meta {meta_preventiva:.2f}%",
            delta_color="normal"
        )
        st.caption("📌 % de manutenção preventiva")
    
    # Comparação entre métodos
    if metodo_atual == "metodo1":
        kpis_metodo2 = calcular_kpis(horas_calendario, horas_preventiva, horas_corretiva, num_falhas, "metodo2")
        st.warning(f"""
        💡 **Comparação:** Se usasse o Método 2 (MTBF/MTTR), a DF seria **{kpis_metodo2['df']:.2f}%** 
        (diferença de {kpis_metodo2['df'] - kpis['df']:+.2f}% pontos percentuais)
        """)
    else:
        kpis_metodo1 = calcular_kpis(horas_calendario, horas_preventiva, horas_corretiva, num_falhas, "metodo1")
        st.warning(f"""
        💡 **Comparação:** Se usasse o Método 1 (DF Total), a DF seria **{kpis_metodo1['df']:.2f}%** 
        (diferença de {kpis_metodo1['df'] - kpis['df']:+.2f}% pontos percentuais)
        """)
    
    # Detalhamento
    st.markdown("---")
    st.subheader("📊 Detalhamento:")
    
    if metodo_atual == "metodo2":
        detalhamento_df = pd.DataFrame({
            'Métrica': [
                'Horas Calendário',
                'Horas Preventiva (programada)',
                'Horas Disponíveis (Calendário - Preventiva)',
                'Horas Corretiva (falhas)',
                'Horas Operadas',
                'Horas Standby',
                '',
                'MTBF (Disponíveis / Falhas)',
                'MTTR (Corretiva / Falhas)',
                'DF = MTBF / (MTBF + MTTR) × 100'
            ],
            'Valor': [
                f"{kpis['horas_calendario']:.2f} h",
                f"{kpis['horas_preventiva']:.2f} h",
                f"{kpis['horas_disponiveis']:.2f} h",
                f"{kpis['horas_corretiva']:.2f} h",
                f"{kpis['horas_operadas']:.2f} h",
                f"{kpis['horas_standby']:.2f} h",
                "",
                f"{kpis['mtbf']:.2f} h",
                f"{kpis['mttr']:.2f} h",
                f"{kpis['df']:.2f}%"
            ]
        })
    else:
        detalhamento_df = pd.DataFrame({
            'Métrica': [
                'Horas Calendário',
                'Horas Manutenção Total',
                '  • Preventiva',
                '  • Corretiva',
                'Horas Operadas',
                'Horas Standby',
                '',
                'DF = (Operadas / Calendário) × 100'
            ],
            'Valor': [
                f"{kpis['horas_calendario']:.2f} h",
                f"{kpis['horas_manutencao_total']:.2f} h",
                f"{kpis['horas_preventiva']:.2f} h",
                f"{kpis['horas_corretiva']:.2f} h",
                f"{kpis['horas_operadas']:.2f} h",
                f"{kpis['horas_standby']:.2f} h",
                "",
                f"{kpis['df']:.2f}%"
            ]
        })
    
    st.dataframe(detalhamento_df, use_container_width=True, hide_index=True)
    
    # Fórmulas
    st.markdown("---")
    st.subheader("📐 Fórmulas Utilizadas")
    
    if metodo_atual == "metodo2":
        st.latex(r"\text{Horas Disponíveis} = \text{Horas Calendário} - \text{Horas Preventiva}")
        st.latex(r"\text{MTBF} = \frac{\text{Horas Disponíveis}}{\text{Número de Falhas}}")
        st.latex(r"\text{MTTR} = \frac{\text{Horas Corretiva}}{\text{Número de Falhas}}")
        st.latex(r"\text{DF} = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}} \times 100")
    else:
        st.latex(r"\text{Horas Operadas} = \text{Horas Calendário} - \text{Horas Preventiva} - \text{Horas Corretiva}")
        st.latex(r"\text{DF} = \frac{\text{Horas Operadas}}{\text{Horas Calendário}} \times 100")
        st.latex(r"\text{MTBF} = \frac{\text{Horas Operadas}}{\text{Número de Falhas}}")
        st.latex(r"\text{MTTR} = \frac{\text{Horas Corretiva}}{\text{Número de Falhas}}")
    
    # Gráficos
    st.markdown("---")
    st.subheader("📊 Visualizações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza - Distribuição de horas
        if metodo_atual == "metodo2":
            labels = ['Horas Operadas', 'Manutenção Preventiva (programada)', 'Manutenção Corretiva (falhas)', 'Standby']
            values = [
                kpis['horas_operadas'],
                kpis['horas_preventiva'],
                kpis['horas_corretiva'],
                kpis['horas_standby']
            ]
            colors = ['#2ecc71', '#3498db', '#e74c3c', '#95a5a6']
        else:
            labels = ['Horas Operadas', 'Manutenção Preventiva', 'Manutenção Corretiva', 'Standby']
            values = [
                kpis['horas_operadas'],
                kpis['horas_preventiva'],
                kpis['horas_corretiva'],
                kpis['horas_standby']
            ]
            colors = ['#2ecc71', '#3498db', '#e74c3c', '#95a5a6']
        
        fig_pizza = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker=dict(colors=colors)
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
    
    if metodo_atual == "metodo1":
        # Método 1: DF = (Horas Operadas / Horas Calendário) * 100
        # Horas Preventiva = Horas Calendário - (DF/100 * Horas Calendário) - Horas Corretiva
        horas_preventiva_necessaria = horas_calendario_reverso - (meta_df_reverso/100 * horas_calendario_reverso) - horas_corretiva_reverso
    else:
        # Método 2: DF = MTBF / (MTBF + MTTR) * 100
        # MTBF = (Horas Calendário - Horas Preventiva) / Num Falhas
        # Resolvendo: Horas Preventiva = Horas Calendário - (MTTR * Num Falhas * DF / (100 - DF))
        if meta_df_reverso >= 100:
            st.error("⚠️ Meta de DF não pode ser 100% com falhas presentes.")
            horas_preventiva_necessaria = -1
        else:
            mtbf_necessario = (mttr_reverso * meta_df_reverso) / (100 - meta_df_reverso)
            horas_disponiveis_necessarias = mtbf_necessario * num_falhas_reverso
            horas_preventiva_necessaria = horas_calendario_reverso - horas_disponiveis_necessarias
    
    if horas_preventiva_necessaria < 0:
        st.error("⚠️ Não é possível atingir a meta de DF com os parâmetros fornecidos. Reduza o número de falhas ou o MTTR.")
    else:
        st.success(f"✅ Para atingir {meta_df_reverso:.2f}% de DF, você precisa de **{horas_preventiva_necessaria:.2f} horas** de manutenção preventiva.")
        
        # Calcular KPIs resultantes
        kpis_reverso = calcular_kpis(
            horas_calendario_reverso,
            horas_preventiva_necessaria,
            horas_corretiva_reverso,
            num_falhas_reverso,
            metodo_atual
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
                num_falhas_sim,
                metodo_atual
            )
            x_label = valor
        elif parametro_variar == "Número de Falhas":
            kpis_temp = calcular_kpis(
                horas_calendario_sim,
                horas_preventiva_sim,
                valor * mttr_sim,
                int(valor),
                metodo_atual
            )
            x_label = valor
        elif parametro_variar == "MTTR":
            kpis_temp = calcular_kpis(
                horas_calendario_sim,
                horas_preventiva_sim,
                num_falhas_sim * valor,
                num_falhas_sim,
                metodo_atual
            )
            x_label = valor
        else:  # Horas Calendário
            kpis_temp = calcular_kpis(
                valor,
                horas_preventiva_sim,
                num_falhas_sim * mttr_sim,
                num_falhas_sim,
                metodo_atual
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
            if metodo_atual == "metodo2":
                # Método 2: DF = MTBF / (MTBF + MTTR)
                df_matrix[i, j] = (mtbf_val / (mtbf_val + mttr_val)) * 100
            else:
                # Método 1: Calcular baseado em horas
                horas_disponiveis = horas_calendario_escala - horas_preventiva_escala
                num_falhas_est = max(1, int(horas_disponiveis / mtbf_val))
                horas_corretiva_est = num_falhas_est * mttr_val
                
                kpis_escala = calcular_kpis(
                    horas_calendario_escala,
                    horas_preventiva_escala,
                    horas_corretiva_est,
                    num_falhas_est,
                    metodo_atual
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

# MODO 5: Curva Característica de Manutenção
elif "Curva Característica" in modo_calculo:
    st.header("📉 Curva Característica de Manutenção")
    
    st.info("""
    🎯 **Objetivo:** Identificar o ponto ótimo para realizar manutenção preventiva baseado na 
    degradação do equipamento ao longo do tempo.
    
    **Conceito:** Após uma preventiva, o equipamento está em condição ótima (MTBF alto). 
    Com o tempo, degrada e o MTBF diminui. Esta análise determina QUANDO intervir novamente.
    """)
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["📤 Upload de Dados", "📊 Análise da Curva", "💡 Recomendações"])
    
    with tab1:
        st.subheader("📤 Carregar Dados da Curva Característica")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file_curva = st.file_uploader(
                "Faça upload do arquivo com dados de degradação",
                type=['xlsx', 'csv'],
                help="Use o template fornecido para coletar os dados"
            )
        
        with col2:
            st.markdown("### 📥 Baixar Template")
            
            # Gerar template
            template_excel = gerar_template_curva_caracteristica()
            
            st.download_button(
                label="📄 Download Template Excel",
                data=template_excel,
                file_name="template_curva_caracteristica.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.markdown("---")
        
        # Instruções rápidas
        with st.expander("📖 Como preencher o template"):
            st.markdown("""
            **Colunas necessárias:**
            
            1. **data_periodo**: Data do período (YYYY-MM-DD)
            2. **semana_apos_preventiva**: Número da semana após preventiva
            3. **tempo_desde_preventiva_horas**: Horas acumuladas desde preventiva
            4. **horas_operadas**: Horas operadas no período
            5. **num_falhas**: Número de falhas no período
            6. **horas_corretiva**: Horas em manutenção corretiva
            7. **mtbf_observado**: MTBF observado (calculado ou medido)
            8. **mttr_observado**: MTTR observado (calculado ou medido)
            9. **observacoes**: Notas sobre o período (opcional)
            
            **Dica:** Colete dados por pelo menos 10-20 períodos após uma preventiva.
            """)
    
    with tab2:
        if uploaded_file_curva is not None:
            try:
                # Carregar dados
                if uploaded_file_curva.name.endswith('.csv'):
                    df_curva = pd.read_csv(uploaded_file_curva)
                else:
                    df_curva = pd.read_excel(uploaded_file_curva)
                
                st.success("✅ Dados carregados com sucesso!")
                
                # Validar colunas
                colunas_necessarias = [
                    'tempo_desde_preventiva_horas', 'horas_operadas', 
                    'num_falhas', 'horas_corretiva'
                ]
                
                colunas_faltantes = [col for col in colunas_necessarias if col not in df_curva.columns]
                
                if colunas_faltantes:
                    st.error(f"⚠️ Colunas faltantes: {', '.join(colunas_faltantes)}")
                else:
                    # Calcular MTBF e MTTR se não existirem
                    if 'mtbf_observado' not in df_curva.columns:
                        df_curva['mtbf_observado'] = df_curva['horas_operadas'] / df_curva['num_falhas']
                    
                    if 'mttr_observado' not in df_curva.columns:
                        df_curva['mttr_observado'] = df_curva['horas_corretiva'] / df_curva['num_falhas']
                    
                    # Calcular DF para cada período
                    df_curva['df_periodo'] = (df_curva['mtbf_observado'] / 
                                              (df_curva['mtbf_observado'] + df_curva['mttr_observado']) * 100)
                    
                    # Preview dos dados
                    st.subheader("📋 Preview dos Dados")
                    st.dataframe(df_curva.head(10), use_container_width=True)
                    
                    st.markdown("---")
                    st.subheader("📊 Análise da Curva de Degradação")
                    
                    # Parâmetros de análise
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        df_alvo = st.number_input(
                            "DF Alvo (%):",
                            min_value=50.0,
                            max_value=99.0,
                            value=85.0,
                            step=1.0,
                            help="Disponibilidade Física desejada"
                        )
                    
                    with col2:
                        custo_preventiva = st.number_input(
                            "Custo Preventiva (R$):",
                            min_value=0.0,
                            value=1000.0,
                            step=100.0,
                            help="Custo de uma manutenção preventiva"
                        )
                    
                    with col3:
                        custo_corretiva = st.number_input(
                            "Custo Corretiva (R$):",
                            min_value=0.0,
                            value=5000.0,
                            step=100.0,
                            help="Custo médio de uma manutenção corretiva"
                        )
                    
                    # Calcular ponto ótimo
                    analise_otimo = calcular_ponto_otimo_intervencao(
                        df_curva.copy(), 
                        df_alvo, 
                        custo_preventiva, 
                        custo_corretiva
                    )
                    
                    # Ajustar curva de degradação
                    x_fit, y_fit, params = ajustar_curva_degradacao(df_curva)
                    
                    st.markdown("---")
                    
                    # Gráfico principal: MTBF vs Tempo
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_mtbf = go.Figure()
                        
                        # Dados observados
                        fig_mtbf.add_trace(go.Scatter(
                            x=df_curva['tempo_desde_preventiva_horas'],
                            y=df_curva['mtbf_observado'],
                            mode='markers',
                            name='MTBF Observado',
                            marker=dict(size=10, color='#3498db'),
                            hovertemplate='Tempo: %{x}h<br>MTBF: %{y:.2f}h<extra></extra>'
                        ))
                        
                        # Curva ajustada
                        fig_mtbf.add_trace(go.Scatter(
                            x=x_fit,
                            y=y_fit,
                            mode='lines',
                            name='Curva de Degradação',
                            line=dict(color='#e74c3c', width=3, dash='dash')
                        ))
                        
                        # Linha do ponto ótimo
                        fig_mtbf.add_vline(
                            x=analise_otimo['tempo_otimo'],
                            line_dash="dot",
                            line_color="green",
                            annotation_text="Ponto Ótimo",
                            annotation_position="top"
                        )
                        
                        # Zonas de operação
                        mtbf_max = df_curva['mtbf_observado'].max()
                        
                        # Zona verde
                        fig_mtbf.add_hrect(
                            y0=mtbf_max * 0.8, y1=mtbf_max * 1.1,
                            fillcolor="green", opacity=0.1,
                            annotation_text="Zona Verde", annotation_position="right"
                        )
                        
                        # Zona amarela
                        fig_mtbf.add_hrect(
                            y0=mtbf_max * 0.5, y1=mtbf_max * 0.8,
                            fillcolor="yellow", opacity=0.1,
                            annotation_text="Zona Amarela", annotation_position="right"
                        )
                        
                        # Zona vermelha
                        fig_mtbf.add_hrect(
                            y0=0, y1=mtbf_max * 0.5,
                            fillcolor="red", opacity=0.1,
                            annotation_text="Zona Vermelha", annotation_position="right"
                        )
                        
                        fig_mtbf.update_layout(
                            title={'text': 'Curva de Degradação - MTBF vs Tempo', 'x': 0.5, 'xanchor': 'center'},
                            xaxis_title='Tempo desde Última Preventiva (horas)',
                            yaxis_title='MTBF (horas)',
                            height=500,
                            hovermode='x unified',
                            showlegend=True
                        )
                        
                        st.plotly_chart(fig_mtbf, use_container_width=True)
                    
                    with col2:
                        # Gráfico DF vs Tempo
                        fig_df = go.Figure()
                        
                        fig_df.add_trace(go.Scatter(
                            x=df_curva['tempo_desde_preventiva_horas'],
                            y=df_curva['df_periodo'],
                            mode='lines+markers',
                            name='DF Observada',
                            line=dict(color='#2ecc71', width=3),
                            marker=dict(size=8)
                        ))
                        
                        # Linha da meta
                        fig_df.add_hline(
                            y=df_alvo,
                            line_dash="dash",
                            line_color="blue",
                            annotation_text=f"Meta: {df_alvo}%",
                            annotation_position="right"
                        )
                        
                        # Ponto ótimo
                        fig_df.add_vline(
                            x=analise_otimo['tempo_otimo'],
                            line_dash="dot",
                            line_color="green",
                            annotation_text="Ponto Ótimo",
                            annotation_position="top"
                        )
                        
                        fig_df.update_layout(
                            title={'text': 'Evolução da Disponibilidade Física', 'x': 0.5, 'xanchor': 'center'},
                            xaxis_title='Tempo desde Última Preventiva (horas)',
                            yaxis_title='Disponibilidade Física (%)',
                            height=500,
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig_df, use_container_width=True)
                    
                    # Gráfico de custos
                    st.markdown("---")
                    st.subheader("💰 Análise de Custos")
                    
                    fig_custos = go.Figure()
                    
                    df_custos = analise_otimo['df_custos']
                    
                    fig_custos.add_trace(go.Scatter(
                        x=df_custos['tempo'],
                        y=df_custos['custo_por_hora'],
                        mode='lines+markers',
                        name='Custo por Hora',
                        line=dict(color='#e67e22', width=3),
                        marker=dict(size=8)
                    ))
                    
                    # Ponto de mínimo custo
                    idx_min_custo = df_custos['custo_por_hora'].idxmin()
                    tempo_min_custo = df_custos.loc[idx_min_custo, 'tempo']
                    custo_min = df_custos.loc[idx_min_custo, 'custo_por_hora']
                    
                    fig_custos.add_vline(
                        x=tempo_min_custo,
                        line_dash="dot",
                        line_color="green",
                        annotation_text=f"Mín Custo: R$ {custo_min:.2f}/h",
                        annotation_position="top"
                    )
                    
                    fig_custos.update_layout(
                        title={'text': 'Custo por Hora de Operação', 'x': 0.5, 'xanchor': 'center'},
                        xaxis_title='Tempo desde Última Preventiva (horas)',
                        yaxis_title='Custo por Hora (R$/h)',
                        height=400,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_custos, use_container_width=True)
                    
                    # Métricas do ponto ótimo
                    st.markdown("---")
                    st.subheader("🎯 Ponto Ótimo de Intervenção")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Tempo Ótimo",
                            f"{analise_otimo['tempo_otimo']:.0f} h",
                            help="Momento ideal para realizar próxima preventiva"
                        )
                        # Converter para dias/semanas
                        dias = analise_otimo['tempo_otimo'] / 24
                        semanas = dias / 7
                        st.caption(f"≈ {dias:.1f} dias ou {semanas:.1f} semanas")
                    
                    with col2:
                        st.metric(
                            "DF no Ponto Ótimo",
                            f"{analise_otimo['df_no_ponto_otimo']:.2f}%",
                            f"{analise_otimo['df_no_ponto_otimo'] - df_alvo:+.2f}% vs meta"
                        )
                    
                    with col3:
                        st.metric(
                            "Custo/Hora Ótimo",
                            f"R$ {analise_otimo['custo_por_hora_otimo']:.2f}",
                            help="Custo por hora de operação no ponto ótimo"
                        )
                    
                    with col4:
                        tempo_max = analise_otimo['tempo_max_alvo']
                        st.metric(
                            "Tempo Máx (Meta DF)",
                            f"{tempo_max:.0f} h" if tempo_max > 0 else "N/A",
                            help="Tempo máximo mantendo DF acima da meta"
                        )
                    
                    # Tabela resumo
                    st.markdown("---")
                    st.subheader("📊 Resumo Estatístico")
                    
                    resumo_curva = pd.DataFrame({
                        'Métrica': [
                            'MTBF Inicial (após preventiva)',
                            'MTBF Final (antes de intervir)',
                            'MTBF Médio',
                            'Degradação Total',
                            'Taxa de Degradação',
                            'MTTR Inicial',
                            'MTTR Final',
                            'Total de Falhas',
                            'DF Inicial',
                            'DF Final',
                            'DF Médio'
                        ],
                        'Valor': [
                            f"{df_curva['mtbf_observado'].iloc[0]:.2f} h",
                            f"{df_curva['mtbf_observado'].iloc[-1]:.2f} h",
                            f"{df_curva['mtbf_observado'].mean():.2f} h",
                            f"{df_curva['mtbf_observado'].iloc[0] - df_curva['mtbf_observado'].iloc[-1]:.2f} h",
                            f"{((df_curva['mtbf_observado'].iloc[0] - df_curva['mtbf_observado'].iloc[-1]) / df_curva['mtbf_observado'].iloc[0] * 100):.1f}%",
                            f"{df_curva['mttr_observado'].iloc[0]:.2f} h",
                            f"{df_curva['mttr_observado'].iloc[-1]:.2f} h",
                            f"{df_curva['num_falhas'].sum()}",
                            f"{df_curva['df_periodo'].iloc[0]:.2f}%",
                            f"{df_curva['df_periodo'].iloc[-1]:.2f}%",
                            f"{df_curva['df_periodo'].mean():.2f}%"
                        ]
                    })
                    
                    st.dataframe(resumo_curva, use_container_width=True, hide_index=True)
            
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        
        else:
            st.warning("📁 Faça upload de um arquivo na aba 'Upload de Dados' para começar a análise.")
    
    with tab3:
        st.subheader("💡 Recomendações e Interpretação")
        
        if uploaded_file_curva is not None and 'df_curva' in locals():
            # Análise automática e recomendações
            mtbf_inicial = df_curva['mtbf_observado'].iloc[0]
            mtbf_final = df_curva['mtbf_observado'].iloc[-1]
            degradacao_pct = ((mtbf_inicial - mtbf_final) / mtbf_inicial * 100)
            df_final = df_curva['df_periodo'].iloc[-1]
            
            st.markdown("### 📋 Análise Automática")
            
            # Status geral
            if df_final >= df_alvo:
                st.success(f"✅ **Status: BOM** - DF atual ({df_final:.2f}%) está acima da meta ({df_alvo}%)")
            elif df_final >= df_alvo * 0.9:
                st.warning(f"⚠️ **Status: ATENÇÃO** - DF atual ({df_final:.2f}%) está próxima da meta ({df_alvo}%)")
            else:
                st.error(f"❌ **Status: CRÍTICO** - DF atual ({df_final:.2f}%) está abaixo da meta ({df_alvo}%)")
            
            st.markdown("---")
            
            # Recomendações baseadas na degradação
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🎯 Recomendações de Ação")
                
                if degradacao_pct > 50:
                    st.error("""
                    **⚠️ AÇÃO URGENTE NECESSÁRIA**
                    
                    O equipamento apresenta degradação severa (> 50%):
                    - ✓ Realizar preventiva IMEDIATAMENTE
                    - ✓ Investigar causa da degradação acelerada
                    - ✓ Considerar troca de componentes críticos
                    - ✓ Revisar procedimentos de manutenção
                    """)
                elif degradacao_pct > 30:
                    st.warning("""
                    **⚠️ PLANEJAR PREVENTIVA**
                    
                    Degradação significativa detectada (30-50%):
                    - ✓ Agendar preventiva nas próximas 2 semanas
                    - ✓ Preparar peças e recursos
                    - ✓ Monitorar falhas de perto
                    - ✓ Documentar padrão de degradação
                    """)
                else:
                    st.success("""
                    **✅ OPERAÇÃO NORMAL**
                    
                    Degradação dentro do esperado (< 30%):
                    - ✓ Continuar monitoramento regular
                    - ✓ Seguir plano de preventiva no ponto ótimo
                    - ✓ Registrar dados para análise futura
                    - ✓ Manter estoque de peças críticas
                    """)
            
            with col2:
                st.markdown("### 📈 Próximos Passos")
                
                tempo_otimo_dias = analise_otimo['tempo_otimo'] / 24
                tempo_atual = df_curva['tempo_desde_preventiva_horas'].iloc[-1]
                tempo_restante = analise_otimo['tempo_otimo'] - tempo_atual
                dias_restantes = tempo_restante / 24
                
                if tempo_restante > 0:
                    st.info(f"""
                    **📅 Cronograma Sugerido:**
                    
                    - Tempo atual: {tempo_atual:.0f}h ({tempo_atual/24:.1f} dias)
                    - Ponto ótimo: {analise_otimo['tempo_otimo']:.0f}h ({tempo_otimo_dias:.1f} dias)
                    - Tempo restante: {tempo_restante:.0f}h ({dias_restantes:.1f} dias)
                    
                    **Ações:**
                    1. Continuar operação por mais {dias_restantes:.0f} dias
                    2. Agendar preventiva para {(datetime.now() + timedelta(days=dias_restantes)).strftime('%d/%m/%Y')}
                    3. Preparar recursos e equipe
                    4. Comunicar parada programada
                    """)
                else:
                    st.error(f"""
                    **⚠️ PRAZO EXCEDIDO**
                    
                    - Tempo atual: {tempo_atual:.0f}h ({tempo_atual/24:.1f} dias)
                    - Ponto ótimo já passou: {abs(tempo_restante):.0f}h atrás
                    
                    **Ação Imediata:**
                    - Realizar preventiva o quanto antes
                    - Equipamento operando além do ideal
                    - Risco aumentado de falhas catastróficas
                    """)
            
            st.markdown("---")
            
            # Comparação com ciclos ideais
            st.markdown("### 📊 Comparação com Padrões")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**🟢 Ciclo Ideal**")
                st.markdown("""
                - MTBF > 150h
                - Degradação < 20%
                - DF > 90%
                - Poucas falhas
                """)
            
            with col2:
                st.markdown("**🟡 Ciclo Aceitável**")
                st.markdown("""
                - MTBF 80-150h
                - Degradação 20-40%
                - DF 80-90%
                - Falhas moderadas
                """)
            
            with col3:
                st.markdown("**🔴 Ciclo Problemático**")
                st.markdown("""
                - MTBF < 80h
                - Degradação > 40%
                - DF < 80%
                - Falhas frequentes
                """)
            
            # Classificação do ciclo atual
            if mtbf_final > 150 and degradacao_pct < 20:
                classificacao = "🟢 IDEAL"
                cor = "success"
            elif mtbf_final > 80 and degradacao_pct < 40:
                classificacao = "🟡 ACEITÁVEL"
                cor = "warning"
            else:
                classificacao = "🔴 PROBLEMÁTICO"
                cor = "error"
            
            if cor == "success":
                st.success(f"**Classificação do Ciclo Atual: {classificacao}**")
            elif cor == "warning":
                st.warning(f"**Classificação do Ciclo Atual: {classificacao}**")
            else:
                st.error(f"**Classificação do Ciclo Atual: {classificacao}**")
            
            st.markdown("---")
            
            # Dicas de melhoria
            st.markdown("### 💡 Dicas para Melhorar o Ciclo")
            
            st.markdown("""
            **Para aumentar o MTBF:**
            - ✓ Melhorar qualidade das preventivas
            - ✓ Usar peças de maior qualidade
            - ✓ Treinar melhor os operadores
            - ✓ Implementar manutenção preditiva
            - ✓ Controlar condições operacionais
            
            **Para reduzir degradação:**
            - ✓ Lubrificação adequada
            - ✓ Limpeza regular
            - ✓ Monitoramento de vibração/temperatura
            - ✓ Evitar sobrecarga do equipamento
            - ✓ Inspeções periódicas
            
            **Para otimizar custos:**
            - ✓ Balancear preventiva vs corretiva
            - ✓ Estocar peças críticas
            - ✓ Treinar equipe de manutenção
            - ✓ Documentar histórico detalhado
            - ✓ Usar dados para decisões
            """)
        
        else:
            st.info("📊 Faça upload dos dados para receber recomendações personalizadas.")
            
            st.markdown("""
            ### 📚 Guia Geral de Interpretação
            
            **🟢 Zona Verde (MTBF > 150h):**
            - Equipamento em excelente condição
            - Poucas falhas esperadas
            - Momento ideal para operação contínua
            
            **🟡 Zona Amarela (MTBF 80-150h):**
            - Degradação normal
            - Monitorar de perto
            - Planejar próxima preventiva
            
            **🟠 Zona Laranja (MTBF 40-80h):**
            - Degradação acelerada
            - Falhas mais frequentes
            - Preventiva necessária em breve
            
            **🔴 Zona Vermelha (MTBF < 40h):**
            - Condição crítica
            - Risco de falha catastrófica
            - Intervenção urgente necessária
            """)

# MODO 6: Análise Histórica
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
                        row['num_falhas'],
                        metodo_atual
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
