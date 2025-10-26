# streamlit_app.py
import streamlit as st
import math

st.set_page_config(page_title="Manutenção – Calculadora de Confiabilidade/Disponibilidade", layout="wide")

st.title("Calculadora de DF, MTBF, MTTR, MTBS e PM")

with st.sidebar:
    st.subheader("Entradas básicas")
    modo = st.selectbox(
        "O que você quer calcular?",
        [
            "Calcular DF e MTBS (dados MTBF, MTTR, I, Dpm)",
            "Calcular MTBF (dados DF, MTTR, I, Dpm)",
            "Calcular MTTR (dados DF, MTBF, I, Dpm)",
            "Calcular I (dados DF, MTBF, MTTR, Dpm)",
            "Calcular Dpm (dados DF, MTBF, MTTR, I)",
        ]
    )
    considerar_pm = st.toggle("Considerar preventivas (I e Dpm)?", value=True)

    mtbf = st.number_input("MTBF (h)", min_value=0.0, value=200.0, step=1.0, format="%.4f")
    mttr = st.number_input("MTTR (h)", min_value=0.0, value=5.0, step=0.5, format="%.4f")
    I = st.number_input("Intervalo de PM – I (h)", min_value=0.0, value=250.0, step=10.0, format="%.4f")
    dpm = st.number_input("Duração PM – Dpm (h)", min_value=0.0, value=4.0, step=0.5, format="%.4f")
    df_alvo = st.number_input("DF alvo (0–1)", min_value=0.0, max_value=1.0, value=0.95, step=0.001, format="%.4f")

    if not considerar_pm:
        I = math.inf
        dpm = 0.0

def safe_div(a, b):
    return a / b if b != 0 and math.isfinite(a) and math.isfinite(b) else math.inf

def calc_df(mtbf, mttr, I, dpm):
    # DF = 1/(1 + MTTR/MTBF + Dpm/I)
    term = (mttr / mtbf) + (dpm / I)
    return 1.0 / (1.0 + term) if math.isfinite(term) else 0.0

def calc_mtbs(mtbf, I):
    # 1 / (1/MTBF + 1/I)
    return 1.0 / ((1.0/mtbf) + (1.0/I)) if math.isfinite(I) and I>0 else mtbf

col1, col2 = st.columns(2)

with col1:
    st.subheader("Resultados")

    if modo == "Calcular DF e MTBS (dados MTBF, MTTR, I, Dpm)":
        DF = calc_df(mtbf, mttr, I, dpm)
        MTBS = calc_mtbs(mtbf, I)
        st.metric("DF (inclui PM)", f"{DF*100:,.2f}%")
        st.metric("MTBS (h)", f"{MTBS:,.2f}")

    elif modo == "Calcular MTBF (dados DF, MTTR, I, Dpm)":
        denom = (1.0/df_alvo) - 1.0 - safe_div(dpm, I)
        if denom > 0:
            mtbf_req = mttr / denom
            st.metric("MTBF necessário (h)", f"{mtbf_req:,.2f}")
            st.caption("Valide se faz sentido operacionalmente.")
        else:
            st.error("Parâmetros inviabilizam o DF alvo (denominador ≤ 0). Ajuste MTTR, I ou Dpm.")

    elif modo == "Calcular MTTR (dados DF, MTBF, I, Dpm)":
        mttr_max = ((1.0/df_alvo) - 1.0 - safe_div(dpm, I)) * mtbf
        if mttr_max >= 0:
            st.metric("MTTR máximo (h)", f"{mttr_max:,.2f}")
        else:
            st.error("DF alvo inviável com MTBF/I/Dpm dados (MTTR sairia negativo).")

    elif modo == "Calcular I (dados DF, MTBF, MTTR, Dpm)":
        denom = (1.0/df_alvo) - 1.0 - (mttr/mtbf)
        if denom > 0:
            I_need = dpm / denom
            st.metric("Intervalo de PM necessário – I (h)", f"{I_need:,.2f}")
        else:
            st.error("DF alvo inviável para MTBF/MTTR dados (denom ≤ 0). Reduza MTTR ou aumente MTBF.")

    elif modo == "Calcular Dpm (dados DF, MTBF, MTTR, I)":
        dpm_max = I * ((1.0/df_alvo) - 1.0 - (mttr/mtbf))
        if dpm_max >= 0:
            st.metric("Duração máxima de PM – Dpm (h)", f"{dpm_max:,.2f}")
        else:
            st.error("DF alvo inviável (Dpm ficaria negativo). Ajuste MTTR, MTBF ou I.")

with col2:
    st.subheader("Checks opcionais (horizonte T)")
    T = st.number_input("Horizonte T (h)", min_value=0.0, value=720.0, step=24.0, format="%.2f")
    if T > 0 and mtbf > 0 and math.isfinite(I):
        Nf = T / mtbf
        Npm = 0 if math.isinf(I) else T / I
        DT_total = Nf*mttr + Npm*dpm
        DF_T = max(0.0, (T - DT_total) / T) if T>0 else 0.0
        st.write(f"Falhas estimadas (Nf): **{Nf:,.2f}**")
        st.write(f"Preventivas (Npm): **{Npm:,.2f}**")
        st.write(f"Downtime total (h): **{DT_total:,.2f}**")
        st.write(f\"DF no período T: **{DF_T*100:,.2f}%**\")

st.caption("Fórmulas: DF = 1 / (1 + MTTR/MTBF + Dpm/I) ; MTBS = 1 / (1/MTBF + 1/I)")
