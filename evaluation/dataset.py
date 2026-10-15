"""Rebuild the frozen, deidentified TCC evaluation corpus from a pinned Git commit.

Only an allowlist of the repository owner's historical synthetic experiments is
processed. This is not a general-purpose anonymizer for private submissions.
Names, email addresses, raw UUIDs, feedback and reasoning chains are excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from evaluation.annotation import annotation_template, canonical_hash, make_packet, synthetic_demo
from evaluation.reliability import evaluate_exports, write_outputs

SOURCE_COMMIT = "79495d00948908503ed4489861ea319a2c7e7972"
SOURCE_REPOSITORY = "https://github.com/savinoo/ai-grading-system"
JSON_SOURCES = {
    "tcc/results/experiment_QA4_9.json": "tcc_qa4_json",
    "tcc/results/experiment_QA4_10.json": "tcc_qa4_json",
    "tcc/results/experiment_QA4_11.json": "tcc_qa4_json",
    "tcc/results/experiment_A_7.json": "tcc_ab_initial",
    "tcc/results/experiment_B_8.json": "tcc_ab_initial",
    "tcc/results/experiment_A_pareado_3.json": "tcc_ab_paired",
    "tcc/results/experiment_B_pareado_4.json": "tcc_ab_paired",
    "tcc/results/experiment_A_final_6.json": "tcc_ab_parallel",
    "tcc/results/experiment_B_final_7.json": "tcc_ab_parallel",
    "tcc/results/experiment_A_v3_13.json": "tcc_ab_v3",
    "tcc/results/experiment_B_v3_14.json": "tcc_ab_v3",
}
NOTEBOOK_AB = ("notebooks/results/cond_A_20260328_163833.json",
               "notebooks/results/cond_B_20260328_163833.json")
NOTEBOOK_QA4 = "notebooks/results/qa4_20260328_163833.json"
NOTEBOOK_QA4_CSV = "notebooks/results/qa4_todas_runs_20260328_163833.csv"
PROTOCOL_SOURCES = ("notebooks/experimento_tcc.ipynb", "run_experiment.py")
CONFIG_FIELDS = ("llm_provider", "llm_model", "llm_temperature", "condition", "rag_enabled",
                 "rag_top_k", "divergence_threshold", "num_questions", "num_students",
                 "discipline", "prompt_version", "source_fingerprints", "workflow_version", "final_status", "mode",
                 "embedding_provider", "embedding_model")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _opaque(kind, value):
    return kind + "-" + _sha(str(value).encode("utf-8"))[:20]


def _select(obj, fields):
    return {key: obj[key] for key in fields if key in obj}


def _dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _criteria(rows):
    # UUIDs and free-form feedback are unnecessary for the analysis.
    return [_select(row, ("name", "description", "weight", "max_score", "score", "raw_score",
                          "weighted_score", "criterion_name", "criterion_description"))
            for row in (rows or [])]


def _context(row, question_id, student_id, *, scope="case"):
    text = row.get("chunk_content", row.get("content", ""))
    text = text if isinstance(text, str) else ""
    result = {"question_uuid": question_id, "student_id": student_id,
              "chunk_content": text[:240], "chunk_sha256": _sha(text.encode("utf-8")),
              "content_characters": len(text), "content_truncated": len(text) > 240,
              "retrieval_scope": scope}
    result.update(_select(row, ("relevance_score", "source_document", "page_number", "chunk_index",
                                "rank", "score", "source", "page")))
    # Store only a basename if a source document happened to contain a local path.
    for field in ("source_document", "source"):
        if isinstance(result.get(field), str):
            result[field] = result[field].replace("\\", "/").split("/")[-1]
    return result


def normalize_export(obj, provenance):
    """Drop identifiers rather than hashing full records that contain identities."""
    questions = []
    qids = {}
    for question in obj.get("questions", []):
        qid = _opaque("q", question.get("statement", question["question_uuid"]))
        qids[str(question["question_uuid"])] = qid
        questions.append({"question_uuid": qid, **_select(question, ("statement", "total_points", "rubric_json",
                                                                     "difficulty", "topic", "discipline"))})
    sids = {str(student["student_id"]): _opaque("response", student["student_id"])
            for student in obj.get("students", [])}
    def ids(row):
        old_q, old_s = str(row["question_uuid"]), str(row["student_id"])
        return {"question_uuid": qids.get(old_q, _opaque("q", old_q)),
                "student_id": sids.get(old_s, _opaque("response", old_s))}
    result = {"schema_version": 1, "id": "historical-" + Path(provenance["source_path"]).stem,
              "provenance": provenance, "response_origin": "synthetic_profiles", "status": obj.get("status"),
              "config": _select(obj.get("config") or {}, CONFIG_FIELDS),
              "questions": questions,
              "students": [{"student_id": sids[str(student["student_id"])],
                            **_select(student, ("quality_profile",))} for student in obj.get("students", [])],
              "answers": [], "corrections": [], "rag_contexts": [], "results": []}
    for answer in obj.get("answers", []):
        result["answers"].append({**ids(answer), **_select(answer, ("answer_text",))})
    for correction in obj.get("corrections", []):
        result["corrections"].append({**ids(correction),
            **_select(correction, ("agent_role", "total_score", "confidence_level", "processing_time_ms",
                                  "latency_ms", "token_usage", "cost_usd", "error")),
            "criterion_scores": _criteria(correction.get("criterion_scores"))})
    for context in obj.get("rag_contexts", []):
        result["rag_contexts"].append(_context(context, **{
            "question_id": ids(context)["question_uuid"], "student_id": ids(context)["student_id"]}))
    for row in obj.get("results", []):
        result["results"].append({**ids(row), **_select(row, (
            "c1_score", "c2_score", "arbiter_score", "divergence_detected", "divergence_value", "final_score",
            "consensus_method", "processing_time_ms", "latency_ms", "token_usage", "cost_usd"))})
    return result


def _notebook_profile(name):
    # These are explicit fictional participant labels in the versioned notebook.
    lowered = (name or "").lower()
    for marker, profile in (("excelente", "excellent"), ("intermedi", "average"),
                            ("fraco", "poor"), ("fora", "off_topic")):
        if marker in lowered:
            return profile
    return "unknown"


def normalize_notebook(raw, provenance, *, condition, rag_enabled, run=None):
    rubric = [{"name": row.get("criterion_name"), "description": row.get("criterion_description"),
               "max_score": row.get("max_score"), "weight": row.get("weight")}
              for row in raw.get("grading_criteria", [])]
    obj = {"schema_version": 1, "id": "historical-" + Path(provenance["source_path"]).stem +
           (f"-r{run}" if run is not None else ""), "provenance": provenance,
           "response_origin": "synthetic_profiles", "status": raw.get("status"),
           "config": {"condition": condition, "rag_enabled": rag_enabled},
           "questions": [], "students": [], "answers": [], "corrections": [], "rag_contexts": [], "results": []}
    students = {}
    for question in raw.get("questions", []):
        qid = _opaque("q", question["statement"])
        obj["questions"].append({"question_uuid": qid, "statement": question["statement"],
            "total_points": question.get("max_score", 10.0), "rubric_json": json.dumps(rubric, ensure_ascii=False)})
        for answer in question.get("student_answers", []):
            sid = _opaque("response", answer["student_uuid"])
            students[sid] = {"student_id": sid, "quality_profile": _notebook_profile(answer.get("student_name"))}
            ids = {"question_uuid": qid, "student_id": sid}
            obj["answers"].append({**ids, "answer_text": answer.get("answer_text")})
            obj["results"].append({**ids, **_select(answer, ("c1_score", "c2_score", "arbiter_score",
                "divergence_detected", "divergence_value", "consensus_method")), "final_score": answer.get("score")})
            for agent in answer.get("agent_criteria_scores", []):
                role = agent.get("agent_id")
                obj["corrections"].append({**ids, "agent_role": role,
                    "total_score": answer.get({"corretor_1": "c1_score", "corretor_2": "c2_score",
                                                "arbitro": "arbiter_score"}.get(role, "unknown")),
                    "criterion_scores": _criteria(agent.get("criteria_scores"))})
            for context in question.get("rag_contexts", []):
                obj["rag_contexts"].append(_context(context, qid, sid, scope="question"))
    obj["students"] = sorted(students.values(), key=lambda row: row["student_id"])
    obj["provenance"]["normalization_notes"] = [
        "Final/c1/c2/divergence fields preserved as exported; inconsistent consensus/divergence metadata is not repaired",
        "Contexts recorded at question level are explicitly assigned to each answer of that question",
        "Model, temperature, actual prompts, runtime and workflow fingerprints unavailable in this source",
    ]
    return obj


def build_dataset(output="evaluation/data", source_ref=SOURCE_COMMIT, repository=None):
    repository = Path(repository) if repository else Path(__file__).resolve().parents[1]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(["git", "rev-parse", "--verify", f"{source_ref}^{{commit}}"],
                                     cwd=repository, text=True).strip()
    source_entries = []
    def source(path, family):
        data = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repository)
        entry = {"source_repository": SOURCE_REPOSITORY, "source_commit": commit,
                 "source_path": path, "source_sha256": _sha(data), "source_family": family,
                 "attribution": "Historical TCC experiments in repository owned by Lucas Lorenzo Savino"}
        source_entries.append(entry)
        return data, dict(entry)
    exports = []
    qa4_paths, notebook_qa4_paths = [], []
    for path, family in JSON_SOURCES.items():
        data, provenance = source(path, family)
        obj = normalize_export(json.loads(data), provenance)
        dest = output / "exports" / Path(path).name
        _dump(dest, obj)
        exports.append(obj)
        if family == "tcc_qa4_json":
            qa4_paths.append(dest)
    for index, path in enumerate(NOTEBOOK_AB):
        data, provenance = source(path, "notebook_ab")
        raw = json.loads(data)
        obj = normalize_notebook(raw["raw_review"], provenance, condition=raw["label"], rag_enabled=raw["rag"])
        _dump(output / "exports" / ("notebook_cond_" + ("A" if index == 0 else "B") + ".json"), obj)
        exports.append(obj)
    data, provenance = source(NOTEBOOK_QA4, "notebook_qa4")
    for run in json.loads(data)["runs"]:
        obj = normalize_notebook(run["raw_review"], dict(provenance), condition=f"QA4 notebook R{run['run']}/3",
                                 rag_enabled=True, run=run["run"])
        dest = output / "exports" / f"notebook_qa4_r{run['run']}.json"
        _dump(dest, obj)
        exports.append(obj)
        notebook_qa4_paths.append(dest)
    source(NOTEBOOK_QA4_CSV, "notebook_qa4_crosscheck")
    for path in PROTOCOL_SOURCES:
        source(path, "versioned_protocol_evidence")
    report = evaluate_exports(qa4_paths)
    report.update(dataset_id="tcc-qa4-json-v1", title="QA4 JSON exports: 3 questions × 4 synthetic profiles × 3 runs",
                  source_commit=commit, response_origin="synthetic_profiles", dataset_kind="historical_observational",
                  limitation="Exact answers absent from all three QA4 JSON exports. Repeatability is descriptive; same-answer identity is unverified.")
    _dump(output / "reliability_report.json", report)
    notebook_report = evaluate_exports(notebook_qa4_paths)
    notebook_report.update(dataset_id="tcc-qa4-notebook-v1", title="QA4 notebook: Q2 only × 4 synthetic profiles × 3 runs",
                           source_commit=commit, response_origin="synthetic_profiles", dataset_kind="historical_observational",
                           limitation="Separate implementation and rubric. Recorded score/divergence/consensus fields contain inconsistencies; examiner fields cannot be assumed to represent canonical final totals.")
    _dump(output / "qa4_notebook_report.json", notebook_report)
    packet = make_packet(exports, "tcc-historical-material-v1")
    _dump(output / "annotation" / "blind_packet.json", packet)
    _dump(output / "annotation" / "ratings_template.json", annotation_template(packet))
    demo_packet, demo_annotations = synthetic_demo()
    _dump(output / "synthetic_demo" / "packet.json", demo_packet)
    _dump(output / "synthetic_demo" / "annotations.json", demo_annotations)
    # The compact tables are reviewable independently of Streamlit.
    write_outputs(report, output / "tables" / "qa4_json")
    write_outputs(notebook_report, output / "tables" / "qa4_notebook")
    generated = [path for path in output.rglob("*") if path.is_file() and path.name != "manifest.json"
                 and (path.parent.name == "exports" or path.name in {
                     "reliability_report.json", "qa4_notebook_report.json", "blind_packet.json", "ratings_template.json",
                     "packet.json", "annotations.json", "corrections.csv", "stability.csv", "report.json"})]
    manifest = {"schema_version": 1, "dataset_version": "1.0.0", "source_commit": commit,
                "source_repository": SOURCE_REPOSITORY, "sources": source_entries,
                "deidentification": {"scope": "Reviewed public synthetic exports only; not a general anonymization guarantee",
                    "excluded": ["student names", "emails", "participant/exam/question UUIDs", "feedback", "reasoning chains", "timestamps"],
                    "identifiers": "Deterministic SHA256 pseudonyms; publicly linkable to public source, not irreversible anonymization",
                    "retrieved_text": "240-character evidence excerpts, exact full-content hash, original length and source/page metadata"},
                "human_reference_status": "absent; no legitimate human annotations found in inspected versioned experiment exports",
                "annotation_cases": len(packet["items"]), "normalized_exports": len(exports),
                "cohorts": [
                    {"dataset_id": "tcc-qa4-json-v1", "correction_rows": report["total_corrections"],
                     "unique_cases": report["unique_cases"], "questions": 3, "runs": 3,
                     "maximum_final_score_range": max(r["score_range"] for r in report["stability"]),
                     "exact_answer_text": "absent; never substituted from A/B exports"},
                    {"dataset_id": "tcc-qa4-notebook-v1", "correction_rows": notebook_report["total_corrections"],
                     "unique_cases": notebook_report["unique_cases"], "questions": 1, "question_label": "Q2", "runs": 3,
                     "maximum_final_score_range": max(r["score_range"] for r in notebook_report["stability"]),
                     "exact_answer_text": "present in raw notebook review exports"}],
                "outputs": [{"path": str(path.relative_to(output)), "sha256": _sha(path.read_bytes())}
                            for path in sorted(generated)]}
    _dump(output / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    builder = commands.add_parser("build")
    builder.add_argument("--source-ref", default=SOURCE_COMMIT, help="Pinned TCC commit; default is frozen source SHA")
    builder.add_argument("--output", default="evaluation/data")
    builder.add_argument("--repository", default=None)
    args = parser.parse_args()
    manifest = build_dataset(args.output, args.source_ref, args.repository)
    print(json.dumps({"source_commit": manifest["source_commit"], "exports": manifest["normalized_exports"],
                      "annotation_cases": manifest["annotation_cases"], "human_references": 0}, indent=2))


if __name__ == "__main__":
    main()
