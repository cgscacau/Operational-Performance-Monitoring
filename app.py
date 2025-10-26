import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import json
import os

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão de Manutenção",
    page_icon="🔧",
    layout="wide"
)

# Inicializar session_state para persistência
if 'dados_historicos' not in st.session_state:
    st.session_state.dados_historicos = []
if 'equipamentos' not in st.session_state:
    st.session_state.equipamentos = ['Equipamento 1', 'Equipamento 2', 'Equipamento 3']

# Funções de cálculo
def calcular_metricas(df):
    """Calcula métricas principais de manutenção"""
    if df.empty:
        return {}
    
    total_horas = len(df)
    horas_operando = len(df[df['status'] == 'Operando'])
    horas_manutencao = len(df[df['status'] == 'Manutenção'])
    horas_paradas = len(df[df['status'] == 'Parado'])
    
    disponibilidade = (horas_operando / total_horas * 100) if total_horas > 0 else 0
    
    # Performance
    producao_real_total = df['producao_real'].sum()
    producao_planejada_total = df['producao_planejada'].sum()
    performance = (producao_real_total / producao_planejada_total * 100) if producao_planejada_total > 0 else 0
    
    # OEE simplificado (assumindo 100% qualidade)
    oee = (disponibilidade * performance) / 10000
    
    # MTBF e MTTR
    paradas = df[df['status'].isin(['Parado', 'Manutenção'])]
    num_paradas = len(paradas)
    mtbf = (total_horas / num_paradas) if num_paradas > 0 else total_horas
    mttr = (horas_manutencao / num_paradas) if num_paradas > 0 else 0
    
    return {
        'disponibilidade': disponibilidade,
        'performance': performance,
        'oee': oee,
        'mtbf': mtbf,
        'mttr': mttr,
        'total_horas': total_horas,
        'horas_operando': horas_operando,
        'horas_manutencao': horas_manutencao,
        'custo_total': df['custo_manutencao'].sum()
    }

def salvar_dados():
    """Salva dados em arquivo JSON"""
    with open('dados_manutencao.json', 'w') as f:
        json.dump(st.session_state.dados_historicos, f, default=str)

def carregar_dados():
    """Carrega dados do arquivo JSON"""
    if os.path.exists('dados_manutencao.json'):
        with open('dados_manutencao.json', 'r') as f:
            st.session_state.dados_historicos = json.load(f)

# Carregar dados ao iniciar
carregar_dados()

# Sidebar - Menu
st.sidebar.title("🔧 Menu Principal")
opcao = st.sidebar.radio(
    "Selecione a opção:",
    ["📝 Registro Horário", "📊 Dashboard", "📈 Análises", "⚙️ Configurações"]
)

# ==================== PÁGINA: REGISTRO HORÁRIO ====================
if opcao == "📝 Registro Horário":
    st.title("📝 Registro Horário de Operação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Novo Registro")
        
        equipamento = st.selectbox("Equipamento", st.session_state.equipamentos)
        data_hora = st.datetime_input("Data e Hora", datetime.now())
        status = st.selectbox("Status", ["Operando", "Parado", "Manutenção"])
        
        producao_planejada = st.number_input("Produção Planejada (unidades/hora)", 
                                            min_value=0, value=100)
        producao_real = st.number_input("Produção Real (unidades/hora)", 
                                       min_value=0, value=0)
        
        if status in ["Parado", "Manutenção"]:
            tempo_parada = st.number_input("Tempo de Parada (minutos)", 
                                          min_value=0, max_value=60, value=0)
            motivo_parada = st.text_input("Motivo da Parada")
            
            if status == "Manutenção":
                tipo_manutencao = st.selectbox("Tipo de Manutenção", 
                                              ["Preventiva", "Corretiva", "Preditiva"])
                custo_manutencao = st.number_input("Custo da Manutenção (R$)", 
                                                  min_value=0.0, value=0.0)
            else:
                tipo_manutencao = ""
                custo_manutencao = 0
        else:
            tempo_parada = 0
            motivo_parada = ""
            tipo_manutencao = ""
            custo_manutencao = 0
        
        observacoes = st.text_area("Observações")
        
        if st.button("💾 Salvar Registro", type="primary"):
            novo_registro = {
                'timestamp': data_hora.isoformat(),
                'equipamento': equipamento,
                'status': status,
                'producao_real': producao_real,
                'producao_planejada': producao_planejada,
                'tempo_parada_min': tempo_parada,
                'motivo_parada': motivo_parada,
                'tipo_manutencao': tipo_manutencao,
                'custo_manutencao': custo_manutencao,
                'observacoes': observacoes
            }
            
            st.session_state.dados_historicos.append(novo_registro)
            salvar_dados()
            st.success("✅ Registro salvo com sucesso!")
            st.rerun()
    
    with col2:
        st.subheader("Últimos Registros")
        if st.session_state.dados_historicos:
            df_recentes = pd.DataFrame(st.session_state.dados_historicos[-10:])
            df_recentes['timestamp'] = pd.to_datetime(df_recentes['timestamp'])
            st.dataframe(df_recentes[['timestamp', 'equipamento', 'status', 
                                     'producao_real', 'tempo_parada_min']], 
                        use_container_width=True)
        else:
            st.info("Nenhum registro encontrado")

# ==================== PÁGINA: DASHBOARD ====================
elif opcao == "📊 Dashboard":
    st.title("📊 Dashboard de Performance")
    
    if not st.session_state.dados_historicos:
        st.warning("⚠️ Nenhum dado disponível. Registre dados na aba 'Registro Horário'.")
    else:
        df = pd.DataFrame(st.session_state.dados_historicos)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            equipamento_filtro = st.multiselect("Equipamento", 
                                               options=df['equipamento'].unique(),
                                               default=df['equipamento'].unique())
        with col2:
            data_inicio = st.date_input("Data Início", 
                                       value=df['timestamp'].min().date())
        with col3:
            data_fim = st.date_input("Data Fim", 
                                    value=df['timestamp'].max().date())
        
        # Aplicar filtros
        df_filtrado = df[
            (df['equipamento'].isin(equipamento_filtro)) &
            (df['timestamp'].dt.date >= data_inicio) &
            (df['timestamp'].dt.date <= data_fim)
        ]
        
        # KPIs principais
        st.subheader("📈 Indicadores Principais")
        
        metricas_totais = calcular_metricas(df_filtrado)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Disponibilidade", 
                     f"{metricas_totais.get('disponibilidade', 0):.1f}%")
        with col2:
            st.metric("Performance", 
                     f"{metricas_totais.get('performance', 0):.1f}%")
        with col3:
            st.metric("OEE", 
                     f"{metricas_totais.get('oee', 0):.1f}%")
        with col4:
            st.metric("MTBF", 
                     f"{metricas_totais.get('mtbf', 0):.1f}h")
        with col5:
            st.metric("MTTR", 
                     f"{metricas_totais.get('mttr', 0):.1f}h")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de status ao longo do tempo
            fig_status = px.histogram(df_filtrado, x='timestamp', color='status',
                                     title='Distribuição de Status ao Longo do Tempo',
                                     barmode='stack')
            st.plotly_chart(fig_status, use_container_width=True)
            
            # Produção real vs planejada
            df_producao = df_filtrado.groupby('timestamp').agg({
                'producao_real': 'sum',
                'producao_planejada': 'sum'
            }).reset_index()
            
            fig_producao = go.Figure()
            fig_producao.add_trace(go.Scatter(x=df_producao['timestamp'], 
                                             y=df_producao['producao_planejada'],
                                             name='Planejada', mode='lines'))
            fig_producao.add_trace(go.Scatter(x=df_producao['timestamp'], 
                                             y=df_producao['producao_real'],
                                             name='Real', mode='lines'))
            fig_producao.update_layout(title='Produção: Real vs Planejada')
            st.plotly_chart(fig_producao, use_container_width=True)
        
        with col2:
            # Pareto de paradas
            paradas = df_filtrado[df_filtrado['motivo_parada'] != '']
            if not paradas.empty:
                pareto_paradas = paradas.groupby('motivo_parada').size().sort_values(ascending=False)
                fig_pareto = px.bar(x=pareto_paradas.index, y=pareto_paradas.values,
                                   title='Pareto de Motivos de Parada',
                                   labels={'x': 'Motivo', 'y': 'Frequência'})
                st.plotly_chart(fig_pareto, use_container_width=True)
            
            # Custos de manutenção
            custos = df_filtrado[df_filtrado['custo_manutencao'] > 0]
            if not custos.empty:
                fig_custos = px.pie(custos, values='custo_manutencao', 
                                   names='tipo_manutencao',
                                   title='Distribuição de Custos por Tipo de Manutenção')
                st.plotly_chart(fig_custos, use_container_width=True)

# ==================== PÁGINA: ANÁLISES ====================
elif opcao == "📈 Análises":
    st.title("📈 Análises Avançadas")
    
    if not st.session_state.dados_historicos:
        st.warning("⚠️ Nenhum dado disponível.")
    else:
        df = pd.DataFrame(st.session_state.dados_historicos)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        tab1, tab2, tab3 = st.tabs(["Análise por Equipamento", 
                                    "Tendências", 
                                    "Previsões"])
        
        with tab1:
            st.subheader("Comparativo entre Equipamentos")
            
            metricas_por_equip = []
            for equip in df['equipamento'].unique():
                df_equip = df[df['equipamento'] == equip]
                metricas = calcular_metricas(df_equip)
                metricas['equipamento'] = equip
                metricas_por_equip.append(metricas)
            
            df_metricas = pd.DataFrame(metricas_por_equip)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(df_metricas, x='equipamento', y='disponibilidade',
                            title='Disponibilidade por Equipamento')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(df_metricas, x='equipamento', y='oee',
                            title='OEE por Equipamento')
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Análise de Tendências")
            
            # Agrupar por dia
            df['data'] = df['timestamp'].dt.date
            tendencia = df.groupby('data').apply(
                lambda x: pd.Series(calcular_metricas(x))
            ).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=tendencia['data'], 
                                    y=tendencia['disponibilidade'],
                                    name='Disponibilidade', mode='lines+markers'))
            fig.add_trace(go.Scatter(x=tendencia['data'], 
                                    y=tendencia['oee'],
                                    name='OEE', mode='lines+markers'))
            fig.update_layout(title='Evolução de Indicadores ao Longo do Tempo',
                            yaxis_title='Percentual (%)')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("Previsões Simples")
            st.info("💡 Com mais dados históricos, podemos implementar "
                   "previsões usando modelos de séries temporais")
            
            # Previsão simples baseada em média móvel
            if len(df) >= 24:  # Pelo menos 24 horas de dados
                df_sorted = df.sort_values('timestamp')
                df_sorted['hora'] = df_sorted['timestamp'].dt.hour
                
                media_por_hora = df_sorted.groupby('hora')['producao_real'].mean()
                
                fig = px.line(x=media_por_hora.index, y=media_por_hora.values,
                             title='Padrão Médio de Produção por Hora do Dia',
                             labels={'x': 'Hora do Dia', 'y': 'Produção Média'})
                st.plotly_chart(fig, use_container_width=True)

# ==================== PÁGINA: CONFIGURAÇÕES ====================
elif opcao == "⚙️ Configurações":
    st.title("⚙️ Configurações")
    
    st.subheader("Gerenciar Equipamentos")
    
    novo_equipamento = st.text_input("Adicionar Novo Equipamento")
    if st.button("➕ Adicionar"):
        if novo_equipamento and novo_equipamento not in st.session_state.equipamentos:
            st.session_state.equipamentos.append(novo_equipamento)
            st.success(f"✅ Equipamento '{novo_equipamento}' adicionado!")
            st.rerun()
    
    st.write("**Equipamentos Cadastrados:**")
    for equip in st.session_state.equipamentos:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"• {equip}")
        with col2:
            if st.button("🗑️", key=f"del_{equip}"):
                st.session_state.equipamentos.remove(equip)
                st.rerun()
    
    st.divider()
    
    st.subheader("Gerenciar Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Exportar Dados (CSV)"):
            if st.session_state.dados_historicos:
                df = pd.DataFrame(st.session_state.dados_historicos)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name=f"dados_manutencao_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with col2:
        if st.button("🗑️ Limpar Todos os Dados", type="secondary"):
            if st.checkbox("Confirmar exclusão"):
                st.session_state.dados_historicos = []
                salvar_dados()
                st.success("✅ Dados limpos!")
                st.rerun()
