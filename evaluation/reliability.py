"""Offline reliability evaluation for ExperimentStore JSON exports.

No model calls, database connection, or third-party packages are required.
No claim of model correctness is made without adjudicated human reference labels.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


def _number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _case_key(question_uuid, student_id):
    return (str(question_uuid), str(student_id))


def _opaque_id(key):
    return hashlib.sha256("|".join(key).encode("utf-8")).hexdigest()[:16]


def _configuration_key(config):
    """Restrict stability grouping to a shared model/retrieval/prompt setup."""
    source = config.get("source_fingerprints") or {}
    keys = {
        "provider": config.get("llm_provider"),
        "model": config.get("llm_model"),
        "temperature": config.get("llm_temperature"),
        "rag_enabled": config.get("rag_enabled"),
        "top_k": config.get("rag_top_k"),
        "examiner_prompt": source.get("examiner_prompt_file_sha256"),
        "examiner_runtime": source.get("examiner_runtime_file_sha256"),
        "retriever": source.get("retriever_file_sha256"),
    }
    # Historical runs frequently lack metadata; that limitation is reported.
    return hashlib.sha256(json.dumps(keys, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def load_gold(path):
    """Gold items must be adjudicated by humans; provisional ratings are ignored."""
    if path is None:
        return {}
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if obj.get("schema_version") != 1 or not isinstance(obj.get("items"), list):
        raise ValueError("Gold file requires schema_version=1 and items array")
    labels = {}
    for item in obj["items"]:
        if item.get("review_status") != "adjudicated":
            continue
        key = _case_key(item["question_uuid"], item["student_id"])
        score = _number(item.get("reference_score"))
        if score is None or not 0 <= score <= 10:
            raise ValueError("Adjudicated reference_score must be between 0 and 10")
        if key in labels:
            raise ValueError("Duplicate adjudicated label for case")
        labels[key] = score
    return labels


def evaluate_exports(paths, gold=None, thresholds=(0.5, 1.0, 1.5, 2.0)):
    """Compute diagnostics and counterfactual arbitration *counts*, not new grades."""
    gold = gold or {}
    records = []
    warnings = []
    observed_groups = defaultdict(list)
    for path in paths:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(obj, dict) or not isinstance(obj.get("results"), list):
            raise ValueError(f"{path}: invalid ExperimentStore export")
        config = obj.get("config") or {}
        source_name = Path(path).name
        experiment_id = str(obj.get("id", source_name))
        signature = _configuration_key(config)
        students = {str(s.get("student_id")): s.get("quality_profile") for s in obj.get("students", [])}
        answers = {
            _case_key(a.get("question_uuid"), a.get("student_id")): a.get("answer_text")
            for a in obj.get("answers", [])
        }
        contexts = defaultdict(int)
        for context in obj.get("rag_contexts", []):
            contexts[_case_key(context.get("question_uuid"), context.get("student_id"))] += 1
        criteria_found = defaultdict(bool)
        for c in obj.get("corrections", []):
            key = _case_key(c.get("question_uuid"), c.get("student_id"))
            criteria_found[key] |= bool(c.get("criterion_scores") or c.get("criteria_scores"))
        if config.get("rag_enabled") is True and not obj.get("rag_contexts"):
            warnings.append(f"{source_name}: RAG enabled but no retrieved contexts in export; do not infer RAG impact")
        if not config.get("source_fingerprints"):
            warnings.append(f"{source_name}: no source/prompt fingerprints (historical metadata)")
        seen = set()
        for row in obj["results"]:
            key = _case_key(row.get("question_uuid"), row.get("student_id"))
            if key in seen:
                raise ValueError(f"{source_name}: duplicate question/student result")
            seen.add(key)
            c1 = _number(row.get("c1_score"))
            c2 = _number(row.get("c2_score"))
            final = _number(row.get("final_score"))
            if c1 is None or c2 is None or final is None:
                warnings.append(f"{source_name}: incomplete score for case {_opaque_id(key)}")
                continue
            if not all(0 <= n <= 10 for n in (c1, c2, final)):
                warnings.append(f"{source_name}: out-of-range score for case {_opaque_id(key)}")
                continue
            delta = abs(c1 - c2)
            human = gold.get(key)
            fail = []
            if delta > 1.0:
                fail.append("high_examiner_disagreement")
            if not criteria_found[key]:
                fail.append("missing_criterion_scores")
            if config.get("rag_enabled") is True and not contexts[key]:
                fail.append("retrieval_evidence_missing")
            if human is None:
                fail.append("no_adjudicated_human_reference")
            elif abs(final - human) > 1.0:
                fail.append("large_reference_error")
            if row.get("arbiter_score") is None and abs(final - (c1 + c2) / 2.0) > 0.01:
                fail.append("consensus_score_inconsistent")
            answer = answers.get(key)
            digest = hashlib.sha256(answer.encode("utf-8")).hexdigest() if isinstance(answer, str) else None
            record = {
                "source": source_name,
                "experiment_id": experiment_id,
                "case_id": _opaque_id(key),
                "profile": students.get(key[1]) or "unknown",
                "configuration_id": signature,
                "c1_score": c1,
                "c2_score": c2,
                "final_score": final,
                "divergence": round(delta, 6),
                "rag_context_count": contexts[key],
                "has_criterion_scores": criteria_found[key],
                "has_answer_text": digest is not None,
                "reference_score": human,
                "absolute_error": round(abs(final - human), 6) if human is not None else None,
                "flags": fail,
            }
            records.append(record)
            condition = str(config.get("condition", "")).strip().upper()
            if condition.startswith("QA4"):
                observed_groups[(signature, key)].append((experiment_id, final, digest, record))
    if not records:
        warnings.append("No valid correction rows")
    simulated = [
        {
            "threshold": threshold,
            "would_trigger": sum(r["divergence"] > threshold for r in records),
            "eligible_rows": len(records),
            "note": "Counterfactual number of arbiter calls; no outcome or improvement measured",
        }
        for threshold in thresholds
    ]
    stability = []
    for (signature, key), entries in sorted(observed_groups.items()):
        if len(entries) < 2 or len({x[0] for x in entries}) < 2:
            continue
        digests = [x[2] for x in entries]
        if all(d is not None for d in digests) and len(set(digests)) != 1:
            warnings.append(f"QA4 case {_opaque_id(key)}: answer text changed; excluded from stability")
            continue
        scores = [x[1] for x in entries]
        verified_same_answer = all(d is not None for d in digests) and len(set(digests)) == 1
        stability.append({
            "configuration_id": signature,
            "case_id": _opaque_id(key),
            "profile": entries[0][3]["profile"],
            "runs": len(scores),
            "score_min": min(scores),
            "score_max": max(scores),
            "score_range": round(max(scores) - min(scores), 6),
            "verified_identical_answer": verified_same_answer,
        })
        if not verified_same_answer:
            warnings.append(f"QA4 case {_opaque_id(key)}: stability descriptive only; answer text absent")
    labelled = [r for r in records if r["absolute_error"] is not None]
    reference_metrics = None
    if labelled:
        errors = [r["final_score"] - r["reference_score"] for r in labelled]
        reference_metrics = {
            "n": len(labelled),
            "mae": round(sum(abs(x) for x in errors) / len(errors), 6),
            "rmse": round(math.sqrt(sum(x * x for x in errors) / len(errors)), 6),
            "bias": round(sum(errors) / len(errors), 6),
            "label_source": "adjudicated reference scores supplied externally",
        }
    return {
        "schema_version": 1,
        "total_corrections": len(records),
        "datasets": len(paths),
        "reference_metrics": reference_metrics,
        "threshold_simulation": simulated,
        "stability": stability,
        "warnings": sorted(set(warnings)),
        "records": records,
    }


def write_outputs(report, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for name, rows in (("corrections.csv", report["records"]), ("stability.csv", report["stability"])):
        if not rows:
            continue
        with (directory / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                writer.writerow({**row, "flags": "|".join(row["flags"])} if "flags" in row else row)


def main():
    parser = argparse.ArgumentParser(description="Offline QA4 and arbitration diagnostics")
    parser.add_argument("exports", nargs="+", help="ExperimentStore JSON exports")
    parser.add_argument("--gold", default=None, help="Optional adjudicated gold-standard JSON")
    parser.add_argument("--output", default="evaluation/output", help="Where to write report and CSVs")
    args = parser.parse_args()
    report = evaluate_exports(args.exports, gold=load_gold(args.gold))
    write_outputs(report, args.output)
    print(json.dumps(
        {
            "total_corrections": report["total_corrections"],
            "qa4_cases": len(report["stability"]),
            "human_reference_evaluated": report["reference_metrics"] is not None,
            "warnings": len(report["warnings"]),
            "output": args.output,
        }, indent=2
    ))


if __name__ == "__main__":
    main()
