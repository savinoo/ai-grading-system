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

from evaluation.annotation import GoldLabels, load_gold, material_hash, reference_for


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
        "embedding_provider": config.get("embedding_provider"),
        "embedding_model": config.get("embedding_model"),
        "divergence_threshold": config.get("divergence_threshold"),
        "prompt_version": config.get("prompt_version"),
        "workflow": source.get("workflow_file_sha256"),
        "arbiter_prompt": source.get("arbiter_prompt_file_sha256"),
        "arbiter_runtime": source.get("arbiter_runtime_file_sha256"),
        "examiner_prompt": source.get("examiner_prompt_file_sha256"),
        "examiner_runtime": source.get("examiner_runtime_file_sha256"),
        "retriever": source.get("retriever_file_sha256"),
    }
    # Historical runs frequently lack metadata; that limitation is reported.
    return hashlib.sha256(json.dumps(keys, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _complete_configuration(config):
    required = ("llm_provider", "llm_model", "llm_temperature", "rag_enabled", "divergence_threshold")
    if any(config.get(name) is None for name in required):
        return False
    fingerprints = config.get("source_fingerprints") or {}
    required_hashes = ["examiner_prompt_file_sha256", "examiner_runtime_file_sha256", "workflow_file_sha256",
                       "arbiter_prompt_file_sha256", "arbiter_runtime_file_sha256"]
    if config.get("rag_enabled"):
        required_hashes.append("retriever_file_sha256")
        if any(config.get(name) is None for name in ("rag_top_k", "embedding_provider", "embedding_model")):
            return False
    return all(isinstance(fingerprints.get(name), str) and len(fingerprints[name]) == 64 and
               all(c in "0123456789abcdef" for c in fingerprints[name]) for name in required_hashes)


def agreement_metrics(pairs):
    """Descriptive continuous-score agreement; correlation alone is not agreement.

    Rows can share a case across runs. No IID confidence interval is reported.
    Pearson and Lin concordance are undefined when their denominator is zero.
    """
    pairs = list(pairs)
    if not pairs:
        return {"n": 0, "mean_absolute_difference": None, "pearson_r": None,
                "lin_concordance": None, "signed_difference_c1_minus_c2": None,
                "exact_agreement_rate": None, "within_0_5_rate": None,
                "within_1_0_rate": None}
    n = len(pairs)
    x, y = zip(*pairs)
    mx, my = sum(x) / n, sum(y) / n
    vx = sum((a - mx) ** 2 for a in x) / n
    vy = sum((b - my) ** 2 for b in y) / n
    cov = sum((a - mx) * (b - my) for a, b in pairs) / n
    differences = [a - b for a, b in pairs]
    denominator = vx + vy + (mx - my) ** 2
    rounded = lambda value: round(value, 6) if value is not None else None
    return {"n": n,
            "mean_absolute_difference": rounded(sum(abs(d) for d in differences) / n),
            "signed_difference_c1_minus_c2": rounded(sum(differences) / n),
            "pearson_r": rounded(cov / math.sqrt(vx * vy)) if vx > 0 and vy > 0 else None,
            "lin_concordance": rounded(2 * cov / denominator) if denominator > 0 else None,
            "exact_agreement_rate": rounded(sum(abs(d) < 1e-9 for d in differences) / n),
            "within_0_5_rate": rounded(sum(abs(d) <= 0.5 + 1e-9 for d in differences) / n),
            "within_1_0_rate": rounded(sum(abs(d) <= 1.0 + 1e-9 for d in differences) / n)}


def evaluate_exports(paths, gold=None, thresholds=(0.5, 1.0, 1.5, 2.0)):
    """Compute diagnostics and counterfactual arbitration *counts*, not new grades."""
    if gold and (not isinstance(gold, GoldLabels) or gold.origin != "human"):
        raise ValueError("Research reference metrics require validated human GoldLabels from load_gold")
    gold = gold if gold is not None else GoldLabels()
    thresholds = tuple(thresholds)
    if any(_number(t) is None or float(t) < 0 for t in thresholds):
        raise ValueError("Thresholds must be finite non-negative numbers")
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
        source_family = (obj.get("provenance") or {}).get("source_family", "unspecified")
        complete_configuration = _complete_configuration(config)
        if not complete_configuration:
            warnings.append(f"{source_name}: configuration evidence incomplete; repeatability is descriptive only")
        students = {str(s.get("student_id")): s.get("quality_profile") for s in obj.get("students", [])}
        questions = {str(q.get("question_uuid")): q for q in obj.get("questions", [])}
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
            human = reference_for(gold, key, questions.get(key[0], {}), answers.get(key))
            if key in gold and human is None:
                warnings.append(f"{source_name}: reference excluded for case {_opaque_id(key)}; exact annotation material unavailable or mismatched")
            fail = []
            reported_delta = _number(row.get("divergence_value"))
            if reported_delta is not None and abs(reported_delta - delta) > 0.011:
                fail.append("exported_divergence_inconsistent")
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
                "source_family": source_family,
                "question_id": key[0] if key[0].startswith("q-") else hashlib.sha256(key[0].encode()).hexdigest()[:16],
                "case_id": _opaque_id(key),
                "profile": students.get(key[1]) or "unknown",
                "configuration_id": signature,
                "verified_complete_configuration": complete_configuration,
                "c1_score": c1,
                "c2_score": c2,
                "final_score": final,
                "divergence": round(delta, 6),
                "exported_divergence": reported_delta,
                "rag_context_count": contexts[key],
                "has_criterion_scores": criteria_found[key],
                "has_answer_text": digest is not None,
                "material_sha256": material_hash(questions.get(key[0], {}), answer),
                "reference_score": human,
                "absolute_error": round(abs(final - human), 6) if human is not None else None,
                "flags": fail,
            }
            records.append(record)
            condition = str(config.get("condition", "")).strip().upper()
            if condition.startswith("QA4"):
                observed_groups[(source_family, signature, key)].append((experiment_id, final, digest, record))
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
    for (source_family, signature, key), entries in sorted(observed_groups.items()):
        if len(entries) < 2 or len({x[0] for x in entries}) < 2:
            continue
        digests = [x[2] for x in entries]
        if len({d for d in digests if d is not None}) > 1:
            warnings.append(f"QA4 case {_opaque_id(key)}: answer text changed; excluded from stability")
            continue
        materials = [x[3]["material_sha256"] for x in entries]
        if len({material for material in materials if material is not None}) > 1:
            warnings.append(f"QA4 case {_opaque_id(key)}: question/rubric/answer material changed; excluded from stability")
            continue
        scores = [x[1] for x in entries]
        verified_same_answer = all(d is not None for d in digests) and len(set(digests)) == 1
        stability.append({
            "configuration_id": signature,
            "source_family": source_family,
            "verified_complete_configuration": all(entry[3]["verified_complete_configuration"] for entry in entries),
            "case_id": _opaque_id(key),
            "profile": entries[0][3]["profile"],
            "runs": len(scores),
            "score_min": min(scores),
            "score_max": max(scores),
            "score_range": round(max(scores) - min(scores), 6),
            "verified_identical_answer": verified_same_answer,
            "verified_identical_material": all(materials) and len(set(materials)) == 1,
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
            "label_source": "evidence-checked adjudicated human reference scores matched to exact annotation material",
            "labelled_unique_cases": len({r["case_id"] for r in labelled}),
            "coverage": round(len(labelled) / len(records), 6),
            "pass_fail_agreement_at_6": round(sum((r["final_score"] >= 6) == (r["reference_score"] >= 6) for r in labelled) / len(labelled), 6),
            "note": "Threshold 6 is an explicit reporting convention, not a validated institutional pass mark",
        }
    return {
        "schema_version": 1,
        "total_corrections": len(records),
        "datasets": len(paths),
        "unique_cases": len({r["case_id"] for r in records}),
        "agreement": {
            **agreement_metrics((r["c1_score"], r["c2_score"]) for r in records),
            "unit": "correction row; repeated cases are not independent observations",
            "interpretation": "Examiner agreement is not grading accuracy; no confidence interval assumes independent rows",
        },
        "agreement_by_profile": {
            profile: agreement_metrics((r["c1_score"], r["c2_score"]) for r in records if r["profile"] == profile)
            for profile in sorted({r["profile"] for r in records})
        },
        "agreement_by_question": {
            question: agreement_metrics((r["c1_score"], r["c2_score"]) for r in records if r["question_id"] == question)
            for question in sorted({r["question_id"] for r in records})
        },
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
