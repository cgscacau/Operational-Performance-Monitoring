# pages/2_Dashboard_Frota.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_icon="📊")

st.title("📊 Dashboard de Gestão de Frota")
st.markdown("Acompanhe e projete a performance de DF da sua frota.")

# --- DADOS DE EXEMPLO ---
# No futuro, isso pode vir de um banco de dados ou um arquivo Excel.
# Por agora, usamos um dicionário para criar a estrutura.
data = {
    'Equipamento': ['PF05', 'PF06', 'PF07'],
    'Corretiva Real': [21.29, 26.00, 106.83],
    'Preventiva Real': [36.00, 238.71, 7.36],
    'Orçado DF': [0.7722, 0.7117, 0.7731],
    'Cor Orç (Mês)': [59.40, 52.80, 54.00],
    'Prev Orç (Mês)': [110.10, 161.70, 114.80],
    'MTBF (h)': [300, 150, 250], # Adicionado para projeção
    'MTTR (h)': [10, 25, 15],     # Adicionado para projeção
}
df = pd.DataFrame(data)

# --- PAINEL DE CONTROLE ---
st.subheader("Painel de Controle")
col1, col2 = st.columns(2)
with col1:
    # Usamos a data do seu exemplo para os cálculos.
    data_base = st.date_input("Selecione a Data do Relatório", datetime(2025, 10, 26))

# --- TABELA INTERATIVA ---
st.markdown("### Dados da Frota (Editáveis)")
st.info("Você pode clicar nas células para editar os valores e ver os cálculos se atualizarem em tempo real.")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)


# --- CÁLCULOS PRINCIPAIS ---
st.markdown("---")
st.subheader("Resultados e Projeções")

try:
    # Constantes de tempo baseadas na data selecionada
    DIA_ATUAL = data_base.day
    DIAS_NO_MES = pd.Timestamp(data_base).days_in_month
    HORAS_TOTAIS_MES = DIAS_NO_MES * 24
    
    # Horas restantes no mês
    dias_restantes = DIAS_NO_MES - DIA_ATUAL
    horas_restantes = dias_restantes * 24

    # 1. Saldo de Horas (Real vs. Orçado até a data)
    edited_df['Cor Orç Acum'] = (edited_df['Cor Orç (Mês)'] / DIAS_NO_MES) * DIA_ATUAL
    edited_df['Prev Orç Acum'] = (edited_df['Prev Orç (Mês)'] / DIAS_NO_MES) * DIA_ATUAL
    edited_df['Saldo Cor'] = edited_df['Cor Orç Acum'] - edited_df['Corretiva Real']
    edited_df['Saldo Prev'] = edited_df['Prev Orç Acum'] - edited_df['Preventiva Real']

    # 2. Projeção de Downtime Corretivo Futuro
    # (Falhas esperadas nas horas restantes * MTTR)
    falhas_esperadas_futuras = horas_restantes / edited_df['MTBF (h)']
    edited_df['hC Prevista (Futuro)'] = falhas_esperadas_futuras * edited_df['MTTR (h)']

    # 3. Projeção de Downtime Total no Mês
    # (O que já aconteceu + O que prevemos que vai acontecer)
    edited_df['Downtime Total Projetado'] = edited_df['Corretiva Real'] + edited_df['Preventiva Real'] + edited_df['hC Prevista (Futuro)']

    # 4. Cálculo da DF Projetada
    edited_df['DF Projetada'] = 1 - (edited_df['Downtime Total Projetado'] / HORAS_TOTAIS_MES)

    # --- EXIBIÇÃO DA TABELA DE RESULTADOS ---
    # Selecionamos e renomeamos as colunas para ficarem parecidas com o seu exemplo
    df_resultados = edited_df[[
        'Equipamento',
        'Saldo Cor',
        'Saldo Prev',
        'hC Prevista (Futuro)',
        'Downtime Total Projetado',
        'Orçado DF',
        'DF Projetada'
    ]].copy()

    # Adicionando a coluna de Diferença
    df_resultados['Diferença'] = df_resultados['DF Projetada'] - df_resultados['Orçado DF']

    # Função para formatar as células
    def format_table(df_to_format):
        return df_to_format.style.format({
            'Saldo Cor': '{:,.2f}',
            'Saldo Prev': '{:,.2f}',
            'hC Prevista (Futuro)': '{:,.2f}',
            'Downtime Total Projetado': '{:,.2f}',
            'Orçado DF': '{:.2%}',
            'DF Projetada': '{:.2%}',
            'Diferença': '{:+.2%}',
        }).background_gradient(
            cmap='RdYlGn', # Vermelho-Amarelo-Verde
            subset=['Diferença'],
            vmin=-0.1, # Limite inferior para a cor
            vmax=0.1   # Limite superior para a cor
        ).background_gradient(
            cmap='RdYlGn_r', # Invertido: Verde é bom (baixo)
            subset=['Downtime Total Projetado']
        )

    st.dataframe(format_table(df_resultados), use_container_width=True)

except Exception as e:
    st.error(f"Ocorreu um erro nos cálculos. Verifique os dados de entrada. Erro: {e}")

