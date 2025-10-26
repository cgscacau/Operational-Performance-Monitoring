# -*- coding: utf-8 -*-
"""
Streamlit – Relatório de Paradas por Frotas e Máquinas

Funcionalidades
- Upload de Excel (múltiplas abas serão combinadas)
- Mapeamento de colunas (auto-sugestão + overrides manuais)
- Resumos por FROTA (CB, TE, PC, MN etc.) e por MÁQUINA
- Mês atual separado do histórico total
- Geração de relatório em HTML e PDF para download

Dependências:
  pip install streamlit pandas numpy openpyxl reportlab

Execute localmente:
  streamlit run app_relatorio_paradas.py
"""
from __future__ import annotations
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

# PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.lib.units import cm

# =========================== Utils ===========================

def normalize_col(c: str) -> str:
    c = str(c).strip().lower()
    c = re.sub(r"\s+", "_", c)
    c = (c
         .replace("ã","a").replace("á","a").replace("â","a").replace("à","a")
         .replace("é","e").replace("ê","e").replace("è","e")
         .replace("í","i").replace("ì","i")
         .replace("ó","o").replace("ô","o").replace("õ","o")
         .replace("ú","u").replace("ü","u")
         .replace("ç","c")
    )
    return c


def read_excel_all_sheets(file_bytes: bytes) -> pd.DataFrame:
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    frames = []
    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet)
            if df is not None and len(df) > 0:
                df["__sheet__"] = sheet
                frames.append(df)
        except Exception:
            pass
    if not frames:
        raise RuntimeError("Nenhuma aba legível encontrada no arquivo.")
    raw = pd.concat(frames, ignore_index=True)
    raw.columns = [normalize_col(c) for c in raw.columns]
    return raw


def pick_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def autodetect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    # date
    date_candidates = [
        "data", "data_inicio", "data_fim", "inicio", "start", "timestamp",
        "dia", "data_da_parada", "data_parada"
    ]
    date_col = pick_col(df, date_candidates)

    # machine
    machine_candidates = [
        "equipamento", "asset", "maquina", "máquina", "prefixo", "tag",
        "codigo", "id", "fleet_number", "unit"
    ]
    machine_col = pick_col(df, [normalize_col(x) for x in machine_candidates])

    # fleet
    fleet_candidates = ["frota", "familia", "familia_equipamento", "tipo", "grupo", "classe", "categoria"]
    fleet_col = pick_col(df, fleet_candidates)

    # downtime (hours)
    downtime_candidates = [
        "horas_paradas", "horas_de_parada", "duracao_horas", "duracao", "duração",
        "downtime_h", "downtime", "tempo_parado_h", "tempo_parado", "horas", "tempo"
    ]
    downtime_col = pick_col(df, [normalize_col(x) for x in downtime_candidates])

    # optional reason
    reason_col = pick_col(df, ["motivo", "causa", "descricao", "descricao_parada", "observacao"])  # noqa

    return {
        "date": date_col,
        "machine": machine_col,
        "fleet": fleet_col,
        "downtime": downtime_col,
        "reason": reason_col,
    }


def infer_fleet_from_machine(code: str) -> str:
    if not isinstance(code, str):
        code = str(code) if code is not None else ""
    m = re.match(r"([A-Za-zÀ-ÿ]+)", code)
    if m:
        return normalize_col(m.group(1)).upper()
    return code[:3].upper() if code else "DESCONHECIDA"


# =========================== Core computations ===========================

def prepare_dataset(raw: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> Tuple[pd.DataFrame, str, str, str, str]:
    df = raw.copy()

    date_col = mapping.get("date")
    machine_col = mapping.get("machine")
    fleet_col = mapping.get("fleet")
    downtime_col = mapping.get("downtime")

    # Date handling
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        mes_col = pick_col(df, ["mes", "mês", "month"]) if "mes" not in df.columns else "mes"
        ano_col = pick_col(df, ["ano", "year"]) if "ano" not in df.columns else "ano"
        if mes_col and ano_col:
            df["__date__"] = pd.to_datetime(df[ano_col].astype(str) + "-" + df[mes_col].astype(str) + "-01",
                                             errors="coerce")
            date_col = "__date__"
        else:
            # fallback
            df["__date__"] = pd.to_datetime("today")
            date_col = "__date__"

    # Machine
    if not machine_col:
        df["__machine__"] = df.index.map(lambda i: f"EQP-{i+1:05d}")
        machine_col = "__machine__"

    # Fleet
    if not fleet_col:
        df["__fleet__"] = df[machine_col].apply(infer_fleet_from_machine)
        fleet_col = "__fleet__"

    # Downtime hours
    if not downtime_col:
        # Try start/end
        start_col = pick_col(df, ["inicio", "hora_inicio", "start_time", "data_inicio"])  # noqa
        end_col   = pick_col(df, ["fim", "hora_fim", "end_time", "data_fim"])  # noqa
        if start_col and end_col:
            df[start_col] = pd.to_datetime(df[start_col], errors="coerce")
            df[end_col]   = pd.to_datetime(df[end_col], errors="coerce")
            df["__downtime_h__"] = (df[end_col] - df[start_col]).dt.total_seconds() / 3600.0
            downtime_col = "__downtime_h__"
        else:
            df["__downtime_h__"] = pd.to_numeric(df.get("horas", np.nan), errors="coerce")
            downtime_col = "__downtime_h__"
    else:
        df[downtime_col] = pd.to_numeric(df[downtime_col], errors="coerce")

    # Sanity
    df[downtime_col] = df[downtime_col].where(
        (df[downtime_col].isna()) | ((df[downtime_col] >= 0) & (df[downtime_col] < 1e6))
    )

    # Periods
    df["ano"] = pd.to_datetime(df[date_col]).dt.year
    df["mes"] = pd.to_datetime(df[date_col]).dt.month
    df["ym"] = pd.to_datetime(df[date_col]).dt.to_period("M")

    return df, date_col, machine_col, fleet_col, downtime_col


def agg_block(frame: pd.DataFrame, level_cols: list[str], downtime_col: str) -> pd.DataFrame:
    tmp = frame.copy()
    tmp["__idx__"] = 1
    res = tmp.groupby(level_cols).agg(
        eventos=("__idx__", "count"),
        horas_paradas=(downtime_col, "sum")
    ).reset_index()
    res["horas_paradas"] = res["horas_paradas"].fillna(0.0)
    res = res.sort_values(["horas_paradas", "eventos"], ascending=[False, False])
    return res


# =========================== Report builders ===========================

def df_to_html_table(df_in: pd.DataFrame, title: str) -> str:
    return f"""
    <h3>{title}</h3>
    {df_in.to_html(index=False, escape=False, float_format=lambda x: f" {x:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))}
    """


def build_html_report(
    by_fleet_cur: pd.DataFrame,
    by_fleet_all: pd.DataFrame,
    by_machine_cur: pd.DataFrame,
    by_machine_all: pd.DataFrame,
    top10_machines_cur: pd.DataFrame,
    source_name: str,
    cur_period: str,
    date_col: str,
    machine_col: str,
    fleet_col: str,
    downtime_col: str,
) -> str:
    total_eventos_cur = int(by_fleet_cur["eventos"].sum()) if len(by_fleet_cur)>0 else 0
    total_horas_cur = float(by_fleet_cur["horas_paradas"].sum()) if len(by_fleet_cur)>0 else 0.0
    total_eventos_all = int(by_fleet_all["eventos"].sum())
    total_horas_all = float(by_fleet_all["horas_paradas"].sum())

    html = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8" />
<title>Relatório de Paradas por Frotas e Máquinas</title>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; margin: 24px; }}
h1, h2, h3 {{ color: #222; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 18px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; }}
th {{ background: #f3f3f3; text-align: left; }}
.caption {{ color: #555; margin-bottom: 10px; }}
.kpi {{ display: inline-block; margin-right: 16px; padding: 6px 10px; background:#f7f7f7; border-radius: 6px; }}
.footer {{ color: #777; font-size: 12px; margin-top: 12px; }}
.small {{ font-size: 12px; color:#666; }}
</style>
</head>
<body>
<h1>Relatório de Paradas – Frotas e Máquinas</h1>
<p class="small">Arquivo fonte: <b>{source_name}</b> &middot; Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>

<h2>Mês atual: {cur_period}</h2>
<div>
  <span class="kpi"><b>Eventos</b>: {total_eventos_cur:,}</span>
  <span class="kpi"><b>Horas paradas</b>: {total_horas_cur:,.2f}</span>
</div>
{df_to_html_table(by_fleet_cur, "Resumo por FROTA – mês atual")}
{df_to_html_table(by_machine_cur, "Resumo por MÁQUINA – mês atual")}
{df_to_html_table(top10_machines_cur, "TOP 10 máquinas por horas paradas – mês atual")}

<h2>Histórico total</h2>
<div>
  <span class="kpi"><b>Eventos</b>: {total_eventos_all:,}</span>
  <span class="kpi"><b>Horas paradas</b>: {total_horas_all:,.2f}</span>
</div>
{df_to_html_table(by_fleet_all, "Resumo por FROTA – histórico")}
{df_to_html_table(by_machine_all, "Resumo por MÁQUINA – histórico")}

<div class="footer">Observações:
<ul>
<li>Heurísticas de colunas: data = <b>{date_col}</b>, máquina = <b>{machine_col}</b>, frota = <b>{fleet_col}</b>, horas = <b>{downtime_col}</b>.</li>
<li>Paradas (eventos) são contadas por linha; horas inválidas/negativas são ignoradas.</li>
<li>Classificação de frota inferida do prefixo da máquina quando ausente (ex.: CB, TE, PC, MN).</li>
</ul>
</div>

</body>
</html>
"""
    return html


def add_df_table_to_story(story, df_in: pd.DataFrame, title_txt: str, styles, max_rows_per_table: int = 30):
    story.append(Paragraph(f"<b>{title_txt}</b>", styles["Heading2"]))
    if df_in.empty:
        story.append(Paragraph("Sem dados.", styles["Normal"]))
        story.append(Spacer(1, 0.4*cm))
        return

    headers = list(df_in.columns)
    rows = df_in.values.tolist()
    for i in range(0, len(rows), max_rows_per_table):
        chunk = rows[i:i+max_rows_per_table]
        table_data = [headers] + chunk
        tbl = Table(table_data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.Color(0.97,0.97,0.97)]),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.4*cm))
    story.append(PageBreak())


def build_pdf_report(
    by_fleet_cur: pd.DataFrame,
    by_fleet_all: pd.DataFrame,
    by_machine_cur: pd.DataFrame,
    by_machine_all: pd.DataFrame,
    top10_machines_cur: pd.DataFrame,
    source_name: str,
    cur_period: str,
    total_eventos_cur: int,
    total_horas_cur: float,
    total_eventos_all: int,
    total_horas_all: float,
) -> bytes:
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("<b>Relatório de Paradas – Frotas e Máquinas</b>", styles["Title"])
    meta = Paragraph(
        f"Fonte: {source_name} &nbsp;&nbsp;•&nbsp;&nbsp; Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"],
    )
    story.extend([title, Spacer(1, 0.3*cm), meta, Spacer(1, 0.6*cm)])

    # KPIs current
    story.append(Paragraph(f"<b>Mês atual: {cur_period}</b>", styles["Heading2"]))
    story.append(Paragraph(
        f"Eventos: {total_eventos_cur:,} &nbsp;&nbsp;|&nbsp;&nbsp; Horas paradas: {total_horas_cur:,.2f}".replace(",", "X").replace(".", ",").replace("X","."),
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.4*cm))
    add_df_table_to_story(story, by_fleet_cur, "Resumo por FROTA – mês atual", styles)
    add_df_table_to_story(story, by_machine_cur, "Resumo por MÁQUINA – mês atual", styles)
    add_df_table_to_story(story, top10_machines_cur, "TOP 10 máquinas por horas paradas – mês atual", styles)

    # KPIs historical
    story.append(Paragraph("<b>Histórico total</b>", styles["Heading2"]))
    story.append(Paragraph(
        f"Eventos: {total_eventos_all:,} &nbsp;&nbsp;|&nbsp;&nbsp; Horas paradas: {total_horas_all:,.2f}".replace(",", "X").replace(".", ",").replace("X","."),
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.4*cm))
    add_df_table_to_story(story, by_fleet_all, "Resumo por FROTA – histórico", styles)
    add_df_table_to_story(story, by_machine_all, "Resumo por MÁQUINA – histórico", styles)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


# =========================== Streamlit App ===========================

st.set_page_config(page_title="Relatório de Paradas – Frotas e Máquinas", layout="wide")
st.title("Relatório de Paradas – Frotas e Máquinas")
st.caption("Envie o Excel, mapeie as colunas (se necessário) e gere os relatórios.")

uploaded = st.file_uploader("Envie o arquivo .xlsx", type=["xlsx"], accept_multiple_files=False)

if uploaded:
    raw = read_excel_all_sheets(uploaded.read())
    st.success(f"Arquivo lido com {len(raw):,} linhas (todas as abas combinadas).")

    # Auto detect
    auto = autodetect_columns(raw)

    with st.expander("Mapeamento de colunas (ajuste se necessário)", expanded=True):
        cols = list(raw.columns)
        date_col = st.selectbox("Coluna de DATA", [None] + cols, index=(cols.index(auto["date"]) + 1) if auto["date"] in cols else 0)
        machine_col = st.selectbox("Coluna de MÁQUINA / Prefixo", [None] + cols, index=(cols.index(auto["machine"]) + 1) if auto["machine"] in cols else 0)
        fleet_col = st.selectbox("Coluna de FROTA / Família", [None] + cols, index=(cols.index(auto["fleet"]) + 1) if auto["fleet"] in cols else 0)
        downtime_col = st.selectbox("Coluna de HORAS PARADAS (h)", [None] + cols, index=(cols.index(auto["downtime"]) + 1) if auto["downtime"] in cols else 0)

    mapping = {"date": date_col, "machine": machine_col, "fleet": fleet_col, "downtime": downtime_col}

    # Prepare
    df, date_c, machine_c, fleet_c, downtime_c = prepare_dataset(raw, mapping)

    # Current month (America/Sao_Paulo timezone implied)
    today = pd.Timestamp.now(tz="America/Sao_Paulo").to_pydatetime()
    cur_period = pd.Period(datetime(today.year, today.month, 1), freq="M")

    df_cur = df[df["ym"] == cur_period].copy()
    df_all = df.copy()

    # Aggregations
    by_fleet_cur = agg_block(df_cur, [fleet_c], downtime_c)
    by_fleet_all = agg_block(df_all, [fleet_c], downtime_c)

    by_machine_cur = agg_block(df_cur, [machine_c, fleet_c], downtime_c)
    by_machine_all = agg_block(df_all, [machine_c, fleet_c], downtime_c)

    top10_machines_cur = by_machine_cur.head(10).copy()

    # KPI row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Eventos (mês)", f"{int(by_fleet_cur['eventos'].sum()):,}")
    kpi2.metric("Horas paradas (mês)", f"{float(by_fleet_cur['horas_paradas'].sum()):,.2f}")
    kpi3.metric("Eventos (hist.)", f"{int(by_fleet_all['eventos'].sum()):,}")
    kpi4.metric("Horas paradas (hist.)", f"{float(by_fleet_all['horas_paradas'].sum()):,.2f}")

    st.subheader("Mês atual – Tabelas")
    st.dataframe(by_fleet_cur, use_container_width=True)
    st.dataframe(by_machine_cur, use_container_width=True)

    st.subheader("Histórico total – Tabelas")
    st.dataframe(by_fleet_all, use_container_width=True)
    st.dataframe(by_machine_all, use_container_width=True)

    # Build reports
    html_report = build_html_report(
        by_fleet_cur, by_fleet_all, by_machine_cur, by_machine_all, top10_machines_cur,
        source_name=uploaded.name,
        cur_period=str(cur_period),
        date_col=date_c,
        machine_col=machine_c,
        fleet_col=fleet_c,
        downtime_col=downtime_c,
    )

    total_eventos_cur = int(by_fleet_cur["eventos"].sum()) if len(by_fleet_cur)>0 else 0
    total_horas_cur = float(by_fleet_cur["horas_paradas"].sum()) if len(by_fleet_cur)>0 else 0.0
    total_eventos_all = int(by_fleet_all["eventos"].sum())
    total_horas_all = float(by_fleet_all["horas_paradas"].sum())

    pdf_bytes = build_pdf_report(
        by_fleet_cur, by_fleet_all, by_machine_cur, by_machine_all, top10_machines_cur,
        source_name=uploaded.name,
        cur_period=str(cur_period),
        total_eventos_cur=total_eventos_cur,
        total_horas_cur=total_horas_cur,
        total_eventos_all=total_eventos_all,
        total_horas_all=total_horas_all,
    )

    # Downloads
    st.download_button(
        label="⬇️ Baixar HTML",
        data=html_report.encode("utf-8"),
        file_name=f"Relatorio_Paradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html",
    )
    st.download_button(
        label="⬇️ Baixar PDF",
        data=pdf_bytes,
        file_name=f"Relatorio_Paradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
    )

else:
    st.info("Envie um arquivo .xlsx para começar.")
