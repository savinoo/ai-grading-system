"""Streamlit viewer for offline Reliability Lab reports.

Start from the repository root:
    streamlit run evaluation/dashboard.py
No model calls or database credentials are required.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
EXAMPLE = ROOT / "examples" / "qa4_historical_report.json"

st.set_page_config(page_title="Reliability Lab | AI Evaluation", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top:2rem;max-width:1350px}
    [data-testid="stMetric"] {background:#122337;border:1px solid #2a4058;
      border-radius:13px;padding:17px 19px}
    [data-testid="stMetricLabel"] {color:#95afc1}
    [data-testid="stMetricValue"] {font-weight:760}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("◈ Reliability Lab")
st.sidebar.caption("Multi-Agent Grading · AI Evaluation")
uploaded_report = st.sidebar.file_uploader(
    "Importar relatório gerado pelo analisador", type=["json"]
)

try:
    if uploaded_report is not None:
        report = json.load(uploaded_report)
        source = f"Importado: {uploaded_report.name}"
    else:
        report = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        source = "Exemplo histórico QA4 · branch tcc"
except (OSError, ValueError, json.JSONDecodeError) as exc:
    st.error(f"Não foi possível abrir o relatório: {exc}")
    st.stop()

if report.get("schema_version") != 1 or not isinstance(report.get("records"), list):
    st.error("Este arquivo não usa o formato do Reliability Evaluation report.json.")
    st.stop()

st.sidebar.caption(source)
st.sidebar.info(
    "Análise offline: nenhum modelo de IA é executado neste dashboard. "
    "Os exports históricos não contêm gold standard humano."
)

st.caption("CASE 01 / EXPERIMENTAL RESEARCH")
st.title("Qualidade que você consegue medir.")
st.write(
    "Avalie divergências entre examinadores, estabilidade das notas e "
    "o custo potencial de acionar o árbitro. "
    "Nenhuma conclusão sobre precisão é feita sem notas humanas adjudicadas."
)

records = pd.DataFrame(report.get("records", []))
stability = pd.DataFrame(report.get("stability", []))
thresholds = pd.DataFrame(report.get("threshold_simulation", []))
human_metrics = report.get("reference_metrics") or {}

max_range = (
    float(stability["score_range"].max())
    if not stability.empty and "score_range" in stability.columns
    else None
)
record_count = int(report.get("total_corrections", len(records)))
if "divergence" in records.columns:
    triggered_at_2 = int((pd.to_numeric(records["divergence"], errors="coerce") > 2).sum())
else:
    triggered_at_2 = None

metric_cols = st.columns(4)
metric_cols[0].metric("Correções avaliadas", str(record_count))
metric_cols[1].metric("Maior oscilação QA4", f"{max_range:.3f} pts" if max_range is not None else "N/D")
metric_cols[2].metric("Acionamentos em > 2,0", str(triggered_at_2) if triggered_at_2 is not None else "N/D")
metric_cols[3].metric("Referência humana", f"{human_metrics['n']} rótulos" if human_metrics else "Pendente")

overview, stability_tab, arbitration_tab, gold_tab = st.tabs(
    ["Visão geral", "Estabilidade QA4", "Simulação de arbitragem", "Gold standard"]
)

with overview:
    a, b = st.columns([1.3, 1])
    with a:
        st.subheader("Divergência média por perfil")
        if not records.empty and {"profile", "divergence"} <= set(records):
            graph = (
                records.assign(divergence=pd.to_numeric(records["divergence"], errors="coerce"))
                .groupby("profile", as_index=False)["divergence"].mean()
                .sort_values("divergence", ascending=False)
            )
            st.bar_chart(graph, x="profile", y="divergence", horizontal=True)
            st.caption("Perfil sintético de resposta, não acurácia do modelo.")
        else:
            st.info("Sem dados de divergência.")
    with b:
        st.subheader("Arbitragem contrafactual")
        if not thresholds.empty and {"threshold", "would_trigger"} <= set(thresholds):
            threshold_choices = sorted(thresholds["threshold"].unique().tolist())
            selected = st.select_slider(
                "Limiar estritamente maior que (pontos)",
                options=threshold_choices,
                value=1.0 if 1.0 in threshold_choices else threshold_choices[-1],
            )
            count = int(
                thresholds.loc[thresholds["threshold"] == selected, "would_trigger"].iloc[0]
            )
            st.metric("Chamadas simuladas ao árbitro", f"{count} / {record_count}")
            st.progress(count / record_count if record_count else 0.0)
            st.warning("Simular um acionamento não mede melhoria de nota.")
        else:
            st.info("Não há simulação de limiares neste relatório.")

    st.subheader("Casos com maior oscilação")
    if not stability.empty:
        display = stability.sort_values("score_range", ascending=False).head(10)
        keep = ["case_id", "profile", "runs", "score_min", "score_max",
                "score_range", "verified_identical_answer"]
        st.dataframe(display[[c for c in keep if c in display]], use_container_width=True, hide_index=True)
    else:
        st.info("Sem execuções repetidas comparáveis no dataset.")

with stability_tab:
    st.subheader("Investigação por caso QA4")
    if stability.empty:
        st.info("Nenhum caso repetido disponível.")
    else:
        profiles = sorted(stability["profile"].dropna().unique().tolist())
        selection = st.selectbox("Filtrar perfil", ["Todos"] + profiles)
        visible = stability if selection == "Todos" else stability[stability["profile"] == selection]
        st.dataframe(
            visible.sort_values("score_range", ascending=False),
            use_container_width=True, hide_index=True,
        )
        unverified = int((~stability["verified_identical_answer"].astype(bool)).sum())
        if unverified:
            st.warning(
                f"{unverified} caso(s) sem comprovação de texto de resposta idêntico "
                "entre execuções nos arquivos importados."
            )

with arbitration_tab:
    st.subheader("Limiar × número de acionamentos")
    if not thresholds.empty:
        st.bar_chart(thresholds, x="threshold", y="would_trigger")
        st.dataframe(thresholds, use_container_width=True, hide_index=True)
    st.info(
        "Uma intervenção só será considerada benéfica quando compararmos "
        "a nota resultante com um gold standard humano validado."
    )

with gold_tab:
    st.subheader("Referências humanas adjudicadas")
    if human_metrics:
        c1, c2, c3 = st.columns(3)
        c1.metric("MAE", human_metrics.get("mae"))
        c2.metric("RMSE", human_metrics.get("rmse"))
        c3.metric("Viés", human_metrics.get("bias"))
        st.caption(f"Somente {human_metrics['n']} caso(s) com referência humana validada.")
    else:
        st.warning("Ainda não há gold standard humano neste relatório.")
        st.markdown(
            "**Protocolo:** seleção de respostas → dupla avaliação cega "
            "→ resolução de discordâncias → nota humana adjudicada → MAE/RMSE."
        )

with st.expander("Limitações e alertas de qualidade dos dados"):
    for warning in report.get("warnings", []):
        st.write(f"• {warning}")
    if not report.get("warnings"):
        st.success("Nenhum alerta registrado no analisador.")

st.download_button(
    "↓ Exportar relatório carregado (JSON)",
    data=json.dumps(report, ensure_ascii=False, indent=2),
    file_name="reliability_lab_report.json",
    mime="application/json",
)
st.caption("Dashboard experimental. Não contém autenticação, dados privados ou chamadas pagas a LLM.")
