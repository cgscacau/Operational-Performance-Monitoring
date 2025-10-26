# pages/2_Dashboard_Frota.py

import streamlit as st
import pandas as pd
from datetime import datetime
from core import processar_dados_frota, formatar_percentual, formatar_horas

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Dashboard de Frota",
    page_icon="📊",
    layout="wide"
)

# ==================== INICIALIZAÇÃO DO SESSION STATE ====================
# Garantir que as configurações globais existam
if 'df_meta' not in st.session_state:
    st.session_state.df_meta = 92.0

# Inicializar dados da frota se não existirem
if 'dados_frota' not in st.session_state:
    # Dados de exemplo baseados na sua planilha
    st.session_state.dados_frota = pd.DataFrame({
        'Equipamento': ['PF05', 'PF06', 'PF07'],
        'Corretiva Real': [21.29, 26.00, 106.83],
        'Preventiva Real': [36.00, 238.71, 7.36],
        'Orçado DF': [77.22, 71.17, 77.31],  # Em percentual
        'Cor Orç (Mês)': [59.40, 52.80, 54.00],
        'Prev Orç (Mês)': [110.10, 161.70, 114.80],
        'MTBF (h)': [300, 150, 250],
        'MTTR (h)': [10, 25, 15]
    })

# ==================== CABEÇALHO ====================
st.title("📊 Dashboard de Gestão de Frota")
st.markdown("Acompanhe o desempenho real vs. orçado e projete a DF de cada equipamento.")

# ==================== PAINEL DE CONTROLE ====================
st.subheader("⚙️ Painel de Controle")

col_ctrl1, col_ctrl2 = st.columns([2, 1])

with col_ctrl1:
    data_relatorio = st.date_input(
        "Data do Relatório",
        value=datetime(2025, 10, 24),
        help="Selecione a data atual para os cálculos de projeção"
    )

with col_ctrl2:
    st.metric(
        "Meta Global de DF",
        f"{st.session_state.df_meta:.1f}%",
        help="Meta definida na página principal"
    )

st.divider()

# ==================== ENTRADA DE DADOS DA FROTA ====================
st.subheader("📝 Dados da Frota")
st.info("✏️ **Instruções:** Clique duas vezes em qualquer célula para editar. Os cálculos serão atualizados automaticamente.")

# Criar colunas de configuração para melhor organização
col_config = {
    'Equipamento': st.column_config.TextColumn(
        'Equipamento',
        help='ID do equipamento',
        width='small'
    ),
    'Corretiva Real': st.column_config.NumberColumn(
        'Corretiva Real (h)',
        help='Horas de manutenção corretiva realizadas até a data',
        format='%.2f',
        min_value=0.0
    ),
    'Preventiva Real': st.column_config.NumberColumn(
        'Preventiva Real (h)',
        help='Horas de manutenção preventiva realizadas até a data',
        format='%.2f',
        min_value=0.0
    ),
    'Orçado DF': st.column_config.NumberColumn(
        'Orçado DF (%)',
        help='Meta de Disponibilidade Física orçada para este equipamento',
        format='%.2f',
        min_value=0.0,
        max_value=100.0
    ),
    'Cor Orç (Mês)': st.column_config.NumberColumn(
        'Orç Corretiva Mensal (h)',
        help='Horas de corretiva orçadas para o mês completo',
        format='%.2f',
        min_value=0.0
    ),
    'Prev Orç (Mês)': st.column_config.NumberColumn(
        'Orç Preventiva Mensal (h)',
        help='Horas de preventiva orçadas para o mês completo',
        format='%.2f',
        min_value=0.0
    ),
    'MTBF (h)': st.column_config.NumberColumn(
        'MTBF (h)',
        help='Tempo Médio Entre Falhas',
        format='%.0f',
        min_value=1
    ),
    'MTTR (h)': st.column_config.NumberColumn(
        'MTTR (h)',
        help='Tempo Médio Para Reparo',
        format='%.0f',
        min_value=1
    )
}

# Editor de dados com configuração personalizada
dados_editados = st.data_editor(
    st.session_state.dados_frota,
    column_config=col_config,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True
)

# Atualizar o session_state com os dados editados
st.session_state.dados_frota = dados_editados

# Botão para adicionar equipamento
if st.button("➕ Adicionar Novo Equipamento"):
    novo_equip = pd.DataFrame({
        'Equipamento': [f'PF{len(dados_editados)+1:02d}'],
        'Corretiva Real': [0.0],
        'Preventiva Real': [0.0],
        'Orçado DF': [st.session_state.df_meta],
        'Cor Orç (Mês)': [50.0],
        'Prev Orç (Mês)': [100.0],
        'MTBF (h)': [300],
        'MTTR (h)': [20]
    })
    st.session_state.dados_frota = pd.concat([st.session_state.dados_frota, novo_equip], ignore_index=True)
    st.rerun()

st.divider()

# ==================== PROCESSAMENTO E CÁLCULOS ====================
st.subheader("📈 Resultados e Projeções")

try:
    # Converter a coluna 'Orçado DF' de percentual para decimal para os cálculos
    dados_para_calculo = dados_editados.copy()
    dados_para_calculo['Orçado DF'] = dados_para_calculo['Orçado DF'] / 100.0
    
    # Processar os dados usando a função do core.py
    resultados = processar_dados_frota(dados_para_calculo, data_relatorio)
    
    # Preparar DataFrame para exibição
    df_exibicao = resultados[[
        'Equipamento',
        'Status',
        'Saldo Cor',
        'Saldo Prev',
        'Downtime Real Total',
        'Downtime Futuro',
        'Orçado DF',
        'DF Projetada',
        'Diferença'
    ]].copy()
    
    # Configuração de colunas para a tabela de resultados
    col_config_resultados = {
        'Equipamento': st.column_config.TextColumn('Equipamento', width='small'),
        'Status': st.column_config.TextColumn('Status', width='small'),
        'Saldo Cor': st.column_config.NumberColumn('Saldo Cor (h)', format='%.2f'),
        'Saldo Prev': st.column_config.NumberColumn('Saldo Prev (h)', format='%.2f'),
        'Downtime Real Total': st.column_config.NumberColumn('Downtime Real (h)', format='%.2f'),
        'Downtime Futuro': st.column_config.NumberColumn('Downtime Projetado (h)', format='%.2f'),
        'Orçado DF': st.column_config.NumberColumn('Orçado DF', format='%.2%'),
        'DF Projetada': st.column_config.NumberColumn('DF Projetada', format='%.2%'),
        'Diferença': st.column_config.NumberColumn('Diferença', format='%.2%')
    }
    
    # Exibir tabela de resultados
    st.dataframe(
        df_exibicao,
        column_config=col_config_resultados,
        use_container_width=True,
        hide_index=True
    )
    
    # ==================== RESUMO DA FROTA ====================
    st.divider()
    st.subheader("📊 Resumo Consolidado da Frota")
    
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    
    with col_r1:
        total_equipamentos = len(resultados)
        equipamentos_ok = len(resultados[resultados['Diferença'] >= 0])
        st.metric(
            "Equipamentos na Meta",
            f"{equipamentos_ok}/{total_equipamentos}",
            delta=f"{(equipamentos_ok/total_equipamentos*100):.1f}%"
        )
    
    with col_r2:
        downtime_total = resultados['Downtime Real Total'].sum()
        st.metric(
            "Downtime Real Total",
            f"{downtime_total:.1f}h"
        )
    
    with col_r3:
        downtime_projetado_total = resultados['Downtime Futuro'].sum()
        st.metric(
            "Downtime Projetado Futuro",
            f"{downtime_projetado_total:.1f}h"
        )
    
    with col_r4:
        df_media_projetada = resultados['DF Projetada'].mean()
        df_media_orcada = resultados['Orçado DF'].mean()
        delta_media = df_media_projetada - df_media_orcada
        st.metric(
            "DF Média Projetada",
            formatar_percentual(df_media_projetada),
            delta=formatar_percentual(delta_media),
            delta_color="normal" if delta_media >= 0 else "inverse"
        )

except Exception as e:
    st.error(f"❌ **Erro nos cálculos:** {str(e)}")
    st.info("Verifique se todos os campos estão preenchidos corretamente e se não há valores inválidos.")
    with st.expander("Detalhes do Erro (para debug)"):
        st.exception(e)

# ==================== RODAPÉ ====================
st.divider()
st.caption(f"📅 Relatório gerado para {data_relatorio.strftime('%d/%m/%Y')} • Dia {data_relatorio.day} do mês")
