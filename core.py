# core.py
"""
Motor de cálculo para o Simulador de Metas Operacionais.
Contém todas as funções matemáticas e de simulação.
"""

import numpy as np
import pandas as pd
from datetime import datetime

# ==================== FUNÇÕES DE DISPONIBILIDADE ====================

def df_from_mtbf_mttr(mtbf, mttr):
    """
    Calcula a Disponibilidade Física (DF) a partir de MTBF e MTTR.
    Funciona com escalares e arrays NumPy.
    """
    denominator = np.add(mtbf, mttr)
    result = np.zeros_like(denominator, dtype=float)
    np.divide(mtbf, denominator, out=result, where=denominator != 0)
    return result


def mttr_for_df(mtbf: float, df_target: float) -> float:
    """Calcula o MTTR necessário para atingir uma meta de DF."""
    if df_target >= 1.0:
        return 0.0
    if df_target <= 0.0:
        return float('inf')
    return mtbf * (1 - df_target) / df_target


def mtbf_for_df(mttr: float, df_target: float) -> float:
    """Calcula o MTBF necessário para atingir uma meta de DF."""
    if df_target >= 1.0:
        return float('inf')
    if df_target <= 0.0:
        return 0.0
    return mttr * df_target / (1 - df_target)


def calculate_operational_df(
    inherent_availability: float, 
    pm_downtime_hours: float, 
    calendar_hours: float
) -> float:
    """Calcula a DF Operacional, considerando paradas para PM."""
    if calendar_hours == 0:
        return inherent_availability
    pm_impact = pm_downtime_hours / calendar_hours
    return max(0, inherent_availability - pm_impact)


# ==================== FUNÇÕES PARA DASHBOARD DE FROTA ====================

def calcular_orcado_acumulado(orcado_mensal: float, dia_atual: int, dias_no_mes: int) -> float:
    """Calcula o orçado acumulado até a data atual proporcionalmente."""
    return (orcado_mensal / dias_no_mes) * dia_atual


def projetar_downtime_futuro(horas_restantes: float, mtbf: float, mttr: float) -> float:
    """
    Projeta as horas de downtime corretivo que ainda devem ocorrer.
    Usa a taxa de falha esperada (horas_restantes / MTBF) * MTTR.
    """
    if mtbf <= 0:
        return 0.0
    falhas_esperadas = horas_restantes / mtbf
    return falhas_esperadas * mttr


def calcular_df_projetada(
    downtime_real_acumulado: float,
    downtime_futuro_projetado: float,
    horas_totais_mes: float
) -> float:
    """Calcula a DF projetada para o final do mês."""
    downtime_total = downtime_real_acumulado + downtime_futuro_projetado
    if horas_totais_mes <= 0:
        return 0.0
    return max(0, 1 - (downtime_total / horas_totais_mes))


def processar_dados_frota(df: pd.DataFrame, data_referencia: datetime) -> pd.DataFrame:
    """
    Processa os dados da frota e calcula todas as métricas derivadas.
    
    Colunas esperadas no DataFrame de entrada:
    - Equipamento
    - Corretiva Real
    - Preventiva Real
    - Orçado DF
    - Cor Orç (Mês)
    - Prev Orç (Mês)
    - MTBF (h)
    - MTTR (h)
    """
    df = df.copy()
    
    # Constantes de tempo
    dia_atual = data_referencia.day
    dias_no_mes = pd.Timestamp(data_referencia).days_in_month
    horas_totais_mes = dias_no_mes * 24
    dias_restantes = dias_no_mes - dia_atual
    horas_restantes = dias_restantes * 24
    
    # 1. Orçado Acumulado até a data
    df['Cor Orç Acum'] = df['Cor Orç (Mês)'].apply(
        lambda x: calcular_orcado_acumulado(x, dia_atual, dias_no_mes)
    )
    df['Prev Orç Acum'] = df['Prev Orç (Mês)'].apply(
        lambda x: calcular_orcado_acumulado(x, dia_atual, dias_no_mes)
    )
    
    # 2. Saldos (Orçado - Real)
    df['Saldo Cor'] = df['Cor Orç Acum'] - df['Corretiva Real']
    df['Saldo Prev'] = df['Prev Orç Acum'] - df['Preventiva Real']
    
    # 3. Downtime Real Acumulado
    df['Downtime Real Total'] = df['Corretiva Real'] + df['Preventiva Real']
    
    # 4. Projeção de Downtime Futuro
    df['Downtime Futuro'] = df.apply(
        lambda row: projetar_downtime_futuro(horas_restantes, row['MTBF (h)'], row['MTTR (h)']),
        axis=1
    )
    
    # 5. DF Projetada
    df['DF Projetada'] = df.apply(
        lambda row: calcular_df_projetada(
            row['Downtime Real Total'],
            row['Downtime Futuro'],
            horas_totais_mes
        ),
        axis=1
    )
    
    # 6. Diferença vs. Orçado
    df['Diferença'] = df['DF Projetada'] - df['Orçado DF']
    
    # 7. Status (atingiu meta ou não)
    df['Status'] = df['Diferença'].apply(lambda x: '🟢' if x >= 0 else '🔴')
    
    return df


# ==================== FUNÇÕES DE FORMATAÇÃO ====================

def formatar_percentual(valor: float) -> str:
    """Formata um número decimal como percentual brasileiro (vírgula)."""
    return f"{valor:.2%}".replace('.', ',')


def formatar_horas(valor: float) -> str:
    """Formata horas com 2 casas decimais no padrão brasileiro."""
    return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
