"""Local, read-only Streamlit viewer for the three offline Lab experiments.

Run: streamlit run evaluation/dashboard.py
This module never invokes a model or a production backend.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def read_object(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Expected a JSON object")
    return obj


def frame(rows, numeric=()):
    result = pd.DataFrame(rows if isinstance(rows, list) else [])
    for column in numeric:
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def table(rows):
    if rows:
        st.dataframe(frame(rows), width="stretch", hide_index=True)
    else:
        st.info("Sem observações elegíveis neste conjunto.")


def main():
    st.set_page_config(page_title="Reliability Lab · Research Case", layout="wide")
    st.markdown("""<style>
    .block-container {padding-top:2rem;max-width:1400px}
    [data-testid="stMetric"] {border:1px solid #62758a55;border-radius:12px;padding:16px}
    [data-testid="stMetricValue"] {font-weight:700}
    </style>""", unsafe_allow_html=True)
    st.sidebar.title("◈ Reliability Lab")
    st.sidebar.caption("Multi-Agent LLM Evaluation")
    options = {"QA4 · exports JSON (36 correções)": DATA / "reliability_report.json",
               "QA4 · notebook Q2 (12 correções)": DATA / "qa4_notebook_report.json"}
    available = {key: value for key, value in options.items() if value.exists()}
    if not available:
        available = {"QA4 · snapshot histórico": ROOT / "examples" / "qa4_historical_report.json"}
    selected = st.sidebar.selectbox("Conjunto de confiabilidade", list(available), key="cohort")
    uploaded = st.sidebar.file_uploader("Carregar outro report.json", type=["json"])
    try:
        report = json.load(uploaded) if uploaded else read_object(available[selected])
        if not isinstance(report, dict) or report.get("schema_version") != 1:
            raise ValueError("Formato esperado: report.json, schema_version=1")
        if not isinstance(report.get("records"), list):
            raise ValueError("O relatório deve conter a lista records")
    except (OSError, ValueError, TypeError) as exc:
        st.error(f"Não foi possível ler o relatório: {exc}")
        st.stop()
    records = frame(report["records"], ("c1_score", "c2_score", "final_score", "divergence"))
    stability = frame(report.get("stability"), ("score_range",))
    thresholds = frame(report.get("threshold_simulation"))
    human = report.get("reference_metrics") or {}
    st.sidebar.info("Execução local e offline. Nos conjuntos históricos incluídos, os perfis de resposta são sintéticos e as notas foram atribuídas por LLMs.")
    st.sidebar.caption("Os dois QA4 têm protocolos diferentes. O seletor troca o conjunto sem somar as amostras.")
    st.caption("AI DATA RESEARCH · REPRODUCIBLE EXPERIMENTS")
    st.title("Multi-Agent Reliability & Evaluation Lab")
    st.write("Onde os examinadores discordam, quando o árbitro seria acionado e o que a evidência de RAG permite concluir.")
    if uploaded:
        st.info(f"Relatório importado: {uploaded.name}. As abas Arbitragem/RAG identificam separadamente os artefatos históricos incluídos no repositório.")
    st.caption(f"Confiabilidade: {selected if not uploaded else uploaded.name} · notas de 0 a 10")
    if report.get("limitation"):
        st.info(report["limitation"])
    cols = st.columns(4)
    cols[0].metric("Correções no conjunto", len(records))
    cases = records["case_id"].nunique() if "case_id" in records else 0
    cols[1].metric("Casos distintos", cases)
    value = stability["score_range"].max() if not stability.empty and "score_range" in stability else None
    cols[2].metric("Maior amplitude entre runs", f"{value:.3f} pts" if value is not None and pd.notna(value) else "N/D")
    cols[3].metric("Referência humana", str(human.get("n", 0)) if human else "Indisponível")
    if not human:
        st.warning("Concordância entre LLMs não mede acurácia. Este relatório não contém gold standard humano validado.")
    reliability, arbitration, rag, provenance = st.tabs([
        "01 · Reliability & Agreement", "02 · Arbitration", "03 · RAG Impact", "Dados & anotação"
    ])
    with reliability:
        left, right = st.columns([1.15, 1])
        with left:
            st.subheader("Divergência absoluta por perfil")
            if {"profile", "divergence"} <= set(records):
                grouped = records.groupby("profile", as_index=False).agg(
                    mean_absolute_difference=("divergence", "mean"), n=("divergence", "count")
                ).sort_values("mean_absolute_difference", ascending=False)
                st.bar_chart(grouped, x="profile", y="mean_absolute_difference", horizontal=True,
                             color="#498de8", x_label="Média |C1 − C2| (pontos)", y_label="Perfil sintético")
                st.dataframe(grouped, width="stretch", hide_index=True)
            else:
                st.info("Scores C1/C2 ausentes neste export; divergência não estimada.")
        with right:
            st.subheader("Medidas de concordância")
            agreement = report.get("agreement") or {}
            if agreement:
                a, b = st.columns(2)
                mad = agreement.get("mean_absolute_difference")
                concordance = agreement.get("lin_concordance")
                a.metric("Diferença média absoluta", f"{mad:.3f} pts" if mad is not None else "N/D")
                b.metric("Concordância de Lin", f"{concordance:.3f}" if concordance is not None else "N/D")
                rates = []
                for field, label in (("exact_agreement_rate", "Notas idênticas"),
                                     ("within_0_5_rate", "Diferença ≤ 0,5 ponto"),
                                     ("within_1_0_rate", "Diferença ≤ 1,0 ponto")):
                    value = agreement.get(field)
                    if value is not None:
                        rates.append({"Medida": label, "Fração de correções": f"{100 * value:.1f}%"})
                st.dataframe(frame(rates), width="stretch", hide_index=True)
                st.caption("Correlações e concordância calculadas sobre correções repetidas; não estimam acurácia contra humanos.")
                with st.expander("Definições e estatísticas completas"):
                    st.json(agreement)
            else:
                st.info("Este conjunto não registra as duas notas individuais necessárias.")
            if human:
                st.subheader("Desvio da referência adjudicada")
                st.json(human)
            st.caption("Correlação pode ser alta mesmo com diferenças sistemáticas. As duas notas usam o mesmo modelo e podem compartilhar erros.")
        st.subheader("Amplitude por caso e configuração")
        if not stability.empty:
            st.bar_chart(stability.sort_values("score_range", ascending=False), x="case_id", y="score_range",
                         color="#498de8", x_label="Caso anônimo", y_label="Máximo − mínimo (pontos)")
            st.dataframe(stability.sort_values("score_range", ascending=False), width="stretch", hide_index=True)
            if "verified_identical_answer" in stability and not stability["verified_identical_answer"].all():
                st.warning("Amplitude descritiva: o texto exato de entrada não foi persistido para comprovar igualdade entre todas as repetições.")
        else:
            st.info("Sem repetições comparáveis.")
        if {"case_id", "profile"} <= set(records):
            profiles = ["Todos"] + sorted(records["profile"].dropna().unique().tolist())
            profile = st.selectbox("Inspecionar correções por perfil", profiles, key="profile")
            visible = records if profile == "Todos" else records[records["profile"] == profile]
            st.dataframe(visible, width="stretch", hide_index=True)
    with arbitration:
        st.subheader("Chamadas sob outros limiares")
        st.caption("Esta simulação usa exclusivamente o conjunto de confiabilidade selecionado acima.")
        if not thresholds.empty and {"threshold", "would_trigger"} <= set(thresholds):
            choices = thresholds["threshold"].tolist()
            choice = st.select_slider("Acionar somente se |C1 − C2| > limiar", options=choices,
                                      value=1.0 if 1.0 in choices else choices[0])
            row = thresholds.loc[thresholds["threshold"] == choice].iloc[0]
            st.metric("Encaminhamentos simulados", f"{int(row['would_trigger'])} / {int(row['eligible_rows'])}")
            st.bar_chart(thresholds, x="threshold", y="would_trigger", color="#498de8",
                         x_label="Limiar estrito (pontos)", y_label="Chamadas simuladas")
            table(report.get("threshold_simulation"))
        else:
            st.info("Sem notas individuais; não é possível simular os acionamentos.")
        st.warning("Uma chamada simulada não demonstra melhora de nota. Não há benefício, custo monetário ou latência de inferência estimados sem observações válidas.")
        supplement("arbitration")
    with rag:
        st.subheader("Comparação histórica A/B e rastros de recuperação")
        st.caption("Análise própria dos pares A/B versionados; não depende do seletor QA4.")
        supplement("rag")
    with provenance:
        st.subheader("Dados versionados e limites")
        st.markdown("Os exports são derivados por uma lista de campos permitidos, com IDs substituídos e hashes de procedência. O QA4 JSON e o QA4 do notebook são preservados separadamente.")
        manifest = DATA / "manifest.json"
        if manifest.exists():
            with st.expander("Manifesto de procedência"):
                st.json(read_object(manifest))
        st.subheader("Anotação humana preparada")
        st.write("Protocolo de duas avaliações independentes, resolução humana de divergências e importação validada. Um formulário vazio não é uma avaliação; exemplos sintéticos são separados dos resultados históricos.")
        st.markdown("Consulte `evaluation/ANNOTATION_PROTOCOL.md` e os materiais em `evaluation/data/annotation/`. Nenhum revisor humano foi presumido ou contratado.")
        with st.expander("Alertas deste conjunto", expanded=True):
            for warning in report.get("warnings", []):
                st.write(f"• {warning}")
            if not report.get("warnings"):
                st.write("Nenhum alerta registrado pelo analisador.")
    st.download_button("Exportar relatório selecionado", json.dumps(report, ensure_ascii=False, indent=2),
                       file_name="reliability_report.json", mime="application/json")
    st.caption("Protótipo de pesquisa local · fontes históricas do TCC · sem deploy em produção")


def supplement(section):
    path = DATA / "experiments.json"
    if not path.exists():
        st.info("Artefato de experimentos não encontrado. Gere-o seguindo evaluation/README.md.")
        return
    try:
        obj = read_object(path)
        data = obj.get(section) or {}
    except (OSError, ValueError) as exc:
        st.error(f"Artefato inválido: {exc}")
        return
    if section == "arbitration":
        st.subheader("Intervenções do árbitro registradas no corpus histórico")
        st.caption("Corpus de inspeção com protocolos diferentes e casos repetidos. Não é uma amostra agrupada para escolher um limiar.")
        cols = st.columns(3)
        cols[0].metric("Correções inspecionadas", data.get("eligible_rows", 0))
        cols[1].metric("Notas de árbitro observadas", data.get("observed_arbiter_rows", 0))
        cols[2].metric("Benefício contra humanos", "Indisponível" if not data.get("reference_comparison") else "Disponível")
        table(data.get("observed_outcomes"))
        st.caption("Movimento da nota em relação à média C1/C2 é descritivo. Árbitros foram selecionados pela divergência; não houve randomização.")
        by_family = obj.get("arbitration_by_source_family") or data.get("by_source_family")
        if by_family:
            with st.expander("Estratificação por protocolo"):
                st.json(by_family)
    else:
        comparisons = data.get("comparisons") or []
        rows = [{key: comparison.get(key) for key in (
            "comparison_id", "exact_material_pairs", "eligible_controlled_pairs",
            "mean_score_shift_descriptive", "mean_divergence_shift_descriptive"
        )} for comparison in comparisons]
        table(rows)
        st.warning("Nenhuma comparação histórica tem todos os controles necessários. Mudança de nota com RAG não estabelece melhora de qualidade.")
        nonempty = [c for c in comparisons if c.get("pairs")]
        if nonempty:
            chosen = st.selectbox("Inspecionar comparação", [c["comparison_id"] for c in nonempty], key="rag_comparison")
            comparison = next(c for c in nonempty if c["comparison_id"] == chosen)
            st.caption(f"Fontes: {comparison.get('source_rag')} / {comparison.get('source_no_rag')}")
            pairs = comparison["pairs"]
            st.bar_chart(frame(pairs), x="rag_case_id", y="score_delta", color="#498de8",
                         x_label="Caso pareado por material exato", y_label="Nota RAG − sem RAG (pontos)")
            st.dataframe(frame([{k: v for k, v in p.items() if k not in ("retrieved_contexts", "blocking_reasons", "flags")}
                               for p in pairs]), width="stretch", hide_index=True)
            pair_id = st.selectbox("Ver evidência de um par", [p["rag_case_id"] for p in pairs], key=f"rag_pair_{chosen}")
            pair = next(p for p in pairs if p["rag_case_id"] == pair_id)
            st.write("**Limites de comparabilidade:** " + ", ".join(pair.get("blocking_reasons") or ["Nenhum registrado"]))
            contexts = pair.get("retrieved_contexts") or []
            if contexts:
                st.write("**Contextos registrados** — trechos reduzidos para inspeção; não são juízos humanos de relevância.")
                for context in contexts:
                    st.caption(f"Página {context.get('page_number', 'N/D')} · fonte {context.get('source_document', 'N/D')} · SHA {context.get('chunk_sha256', 'N/D')}")
                    st.text(context.get("excerpt") or "Trecho ausente")
            else:
                st.info("Não há contexto recuperado persistido para este par.")
        st.caption(data.get("limitation", ""))
    with st.expander("Diagnósticos e artefato completo"):
        flags = {}
        for row in obj.get("failures", []):
            for flag in row.get("flags", []):
                flags[flag] = flags.get(flag, 0) + 1
        table([{"diagnostic_flag": flag, "affected_rows": count} for flag, count in sorted(flags.items())])
        st.json(data, expanded=False)


if __name__ == "__main__":
    main()
