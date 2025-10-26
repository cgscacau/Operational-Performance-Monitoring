# core.py

import numpy as np

def df_from_mtbf_mttr(mtbf, mttr):
    """
    Calcula a Disponibilidade Física (DF) a partir de MTBF e MTTR.
    Esta versão é "vetorizada" para funcionar com números únicos (floats) e arrays NumPy.
    """
    # np.add garante que a operação funcione para escalares e arrays.
    denominator = np.add(mtbf, mttr)
    
    # Prepara um array de saída com o mesmo formato da entrada, preenchido com zeros.
    # Se a entrada for escalar, np.zeros_like cria um escalar 0.0.
    # Se for array, cria um array de zeros. Isso resolve o caso de divisão por zero.
    result = np.zeros_like(denominator, dtype=float)

    # np.divide é a forma segura de fazer divisão por elemento em NumPy.
    # Onde a condição 'where' for False (denominador == 0), o valor do 'out' (result) é mantido (ou seja, 0).
    # Onde for True, a divisão é calculada e inserida no 'out' (result).
    np.divide(mtbf, denominator, out=result, where=denominator != 0)
    
    return result


def mttr_for_df(mtbf: float, df_target: float) -> float:
    """Calcula o MTTR necessário para atingir uma meta de DF, dado um MTBF."""
    if df_target >= 1.0:
        return 0.0
    if df_target <= 0.0:
        return float('inf')
    return mtbf * (1 - df_target) / df_target

def mtbf_for_df(mttr: float, df_target: float) -> float:
    """Calcula o MTBF necessário para atingir uma meta de DF, dado um MTTR."""
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
    """Calcula a DF Operacional, considerando as paradas para PM."""
    if calendar_hours == 0:
        return inherent_availability
    
    pm_impact = pm_downtime_hours / calendar_hours
    return inherent_availability - pm_impact

def calculate_production(
    capacity_per_hour: float,
    operational_df: float,
    utilization_factor: float,
    calendar_hours: float = 8760
) -> float:
    """Calcula a produção anual prevista."""
    operating_hours = calendar_hours * operational_df * utilization_factor
    return capacity_per_hour * operating_hours

