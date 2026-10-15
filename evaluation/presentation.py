"""Build a source-backed portable-report manifest from reviewed Lab artifacts.

The Markdown technical report remains readable on GitHub. The optional portable
reader is generated from this manifest by the Data Analytics report packager.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build_artifact(data=ROOT / "data"):
    data = Path(data)
    reliability = json.loads((data / "reliability_report.json").read_text())
    notebook = json.loads((data / "qa4_notebook_report.json").read_text())
    experiments = json.loads((data / "experiments.json").read_text())
    source_commit = reliability["source_commit"]
    repo = "https://github.com/savinoo/ai-grading-system"
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE qa4_json_corrections (case_id TEXT, profile TEXT, configuration_id TEXT, c1_score REAL, c2_score REAL, final_score REAL)")
    connection.executemany("INSERT INTO qa4_json_corrections VALUES (?, ?, ?, ?, ?, ?)",
                           [(r["case_id"], r["profile"], r["configuration_id"], r["c1_score"], r["c2_score"], r["final_score"])
                            for r in reliability["records"]])
    connection.execute("CREATE TABLE threshold_candidates (threshold REAL)")
    connection.executemany("INSERT INTO threshold_candidates VALUES (?)", [(r["threshold"],) for r in reliability["threshold_simulation"]])
    connection.execute("CREATE TABLE historical_rag_pairs (comparison_id TEXT, score_delta REAL, divergence_delta REAL, eligible INTEGER)")
    connection.executemany("INSERT INTO historical_rag_pairs VALUES (?, ?, ?, ?)",
                           [(c["comparison_id"], p["score_delta"], p["divergence_delta"], int(p["eligible_controlled_comparison"]))
                            for c in experiments["rag"]["comparisons"] for p in c["pairs"]])
    queries = {
        "profile_agreement": "SELECT profile, COUNT(*) AS correction_rows, AVG(ABS(c1_score-c2_score)) AS mean_absolute_difference, AVG(c1_score-c2_score) AS signed_difference, SUM(ABS(c1_score-c2_score)<=0.5) AS within_0_5_rows, 10 AS scale_max FROM qa4_json_corrections GROUP BY profile ORDER BY mean_absolute_difference DESC",
        "qa4_ranges": "SELECT case_id, SUBSTR(case_id,1,8) AS case_label, profile, configuration_id, COUNT(*) AS runs, MIN(final_score) AS score_min, MAX(final_score) AS score_max, MAX(final_score)-MIN(final_score) AS score_range FROM qa4_json_corrections GROUP BY case_id, profile, configuration_id ORDER BY score_range DESC",
        "qa4_thresholds": "SELECT threshold, '> ' || PRINTF('%.1f',threshold) AS threshold_label, COUNT(*) AS eligible_rows, SUM(ABS(c1_score-c2_score)>threshold) AS would_trigger FROM qa4_json_corrections CROSS JOIN threshold_candidates GROUP BY threshold ORDER BY threshold",
        "rag_comparisons": "SELECT comparison_id, COUNT(*) AS exact_material_pairs, SUM(eligible) AS eligible_controlled_pairs, AVG(score_delta) AS mean_score_shift_descriptive, AVG(divergence_delta) AS mean_divergence_shift_descriptive FROM historical_rag_pairs GROUP BY comparison_id ORDER BY comparison_id",
    }
    datasets = {key: [dict(row) for row in connection.execute(sql)] for key, sql in queries.items()}
    connection.close()
    datasets["cohorts"] = [
        {"cohort": "QA4 JSON", "rows": reliability["total_corrections"], "cases": reliability["unique_cases"],
         "max_range": max(r["score_range"] for r in reliability["stability"]), "answer_identity": "unverified: exact answers absent"},
        {"cohort": "QA4 notebook Q2", "rows": notebook["total_corrections"], "cases": notebook["unique_cases"],
         "max_range": max(r["score_range"] for r in notebook["stability"]), "answer_identity": "exact material present; scoring-field inconsistencies"},
    ]
    sources = []
    for key, sql in queries.items():
        is_rag = key == "rag_comparisons"
        sources.append({"id": key, "label": "Exact-material RAG pair aggregation" if is_rag else "QA4 JSON correction aggregation",
                        "path": "evaluation/data/experiments.json" if is_rag else "evaluation/data/reliability_report.json",
                        "query": {"language": "sql", "engine": "SQLite in-memory; materialized from reviewed deidentified report rows",
                                  "sql": sql, "description": "Executed by evaluation/presentation.py. RAG material pairing is performed by evaluation/experiments.py; QA4 rows by evaluation/reliability.py.",
                                  "tables_used": ["historical_rag_pairs"] if is_rag else ["qa4_json_corrections", "threshold_candidates"],
                                  "filters": ["Historical valid score rows; QA4 cohorts kept separate; no human reference labels"],
                                  "metric_definitions": {"mean_absolute_difference": "mean(abs(c1_score-c2_score)); 0–10 points",
                                                         "score_range": "max(final_score)-min(final_score) within case/configuration",
                                                         "would_trigger": "count(abs(c1_score-c2_score)>threshold)",
                                                         "mean_score_shift_descriptive": "mean(final_score_rag-final_score_no_rag) within exact-material pairs; not quality or causal effect"}}})
    sources.append({"id": "manifest", "label": "Pinned original TCC source and lineage", "path": "evaluation/data/manifest.json",
                    "url": f"{repo}/tree/{source_commit}"})
    charts = [
        ("disagreement", "Mean examiner disagreement by synthetic profile", "QA4 JSON · 9 rows per profile · 0–10 score scale", "profile_agreement", "profile", "mean_absolute_difference", "Profile", "Mean |C1 − C2| (points)", "profile_agreement"),
        ("ranges", "Recorded final-score range by case", "QA4 JSON · three repetitions per case · identical answers unverified", "qa4_ranges", "case_label", "score_range", "Anonymous case", "Maximum − minimum (points)", "qa4_ranges"),
        ("thresholds", "Counterfactual arbitration referrals", "QA4 JSON · 36 rows · strict thresholds · no new arbiter outcomes", "qa4_thresholds", "threshold_label", "would_trigger", "Strict disagreement threshold", "Simulated referrals", "qa4_thresholds"),
        ("rag_deltas", "Descriptive RAG minus no-RAG score shifts", "12 exact-material pairs per comparison · zero fully controlled historical pairs", "rag_comparisons", "comparison_id", "mean_score_shift_descriptive", "Historical comparison", "Mean grade shift (points)", "rag_comparisons"),
    ]
    chart_specs = [{"id": cid, "title": title, "subtitle": subtitle, "type": "bar", "dataset": dataset,
                    "sourceId": source, "valueFormat": "number",
                    "palette": {"kind": "sequential", "name": "blue"}, "labels": {"values": "auto"},
                    "encodings": {"x": {"field": x, "type": "nominal", "label": xl},
                                  "y": {"field": y, "type": "quantitative", "label": yl}}}
                   for cid, title, subtitle, dataset, x, y, xl, yl, source in charts]
    text = (ROOT / "TECHNICAL_REPORT.md").read_text()
    sections = text.split("\n## ")
    blocks = [{"id": "title", "type": "markdown", "body": sections[0].strip()}]
    inserts = {"Experiment 1": ["disagreement", "ranges"], "Experiment 2": ["thresholds"], "Experiment 3": ["rag_deltas"]}
    for index, section in enumerate(sections[1:]):
        blocks.append({"id": f"section_{index}", "type": "markdown", "body": "## " + section.strip()})
        for key, chart_ids in inserts.items():
            if section.startswith(key):
                for chart_id in chart_ids:
                    blocks.append({"id": f"figure_{chart_id}", "type": "chart", "chartId": chart_id})
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {"surface": "report", "manifest": {"version": 1, "surface": "report",
            "title": "Multi-Agent LLM Reliability & Evaluation Lab", "generatedAt": generated,
            "description": "Historical results, controlled-comparison limits and reproducible evaluation methods.",
            "blocks": blocks, "cards": [], "charts": chart_specs, "tables": [], "sources": sources},
            "snapshot": {"version": 1, "generatedAt": generated, "status": "partial", "datasets": datasets,
                         "accessIssues": [{"id": "human_reference_absent", "dataset": "human_references",
                                           "message": "No validated human grades in the accessible study exports. Accuracy and human-relative arbitration/RAG benefit remain unmeasured."}]},
            "sources": sources}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=str(ROOT / "data"))
    parser.add_argument("--output", default=str(ROOT / "artifacts" / "report.artifact.json"))
    args = parser.parse_args()
    artifact = build_artifact(args.data)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
