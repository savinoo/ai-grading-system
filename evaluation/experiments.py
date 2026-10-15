"""Offline arbitration replay and evidence-gated RAG comparisons.

These analyses never call a model. A missing arbiter score cannot be replayed,
agreement is not accuracy, and a changed grade is not a quality improvement.
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
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _mean(values):
    return round(sum(values) / len(values), 6) if values else None


def _measurement(value):
    number = _number(value)
    return number if number is not None and number >= 0 else None


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _valid_sha256(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _key(item):
    return str(item.get("question_uuid")), str(item.get("student_id"))


def _case_id(key):
    return hashlib.sha256("|".join(key).encode()).hexdigest()[:16]


def _rubric(question):
    value = question.get("rubric_json", question.get("rubric"))
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    # Database row identifiers are not rubric content. Everything else matters.
    if isinstance(value, list) and value:
        return [{k: v for k, v in item.items()
                 if k not in {"id", "uuid", "criterion_uuid", "question_uuid", "experiment_id"}}
                if isinstance(item, dict) else item for item in value]
    return None


def _material(question, answer):
    rubric = _rubric(question)
    points = _number(question.get("total_points", question.get("max_score")))
    statement = question.get("statement")
    if not isinstance(statement, str) or not statement or rubric is None or points is None:
        return None
    if not isinstance(answer, str) or not answer:
        return None
    # A declared controlled fixture must carry real rubric scales too.
    from evaluation.annotation import material_hash
    if material_hash({"statement": statement, "rubric": rubric, "total_points": points}, answer) is None:
        return None
    return _digest({"statement": statement, "rubric": rubric,
                    "points": points, "answer": answer})


def _consensus(c1, c2, arbiter):
    """Mirror the repository's closest-pair rule, including its high-pair tie."""
    low, middle, high = sorted((c1, c2, arbiter))
    return (low + middle) / 2 if middle - low < high - middle else (middle + high) / 2


def _reference(gold, key, question, answer):
    if not gold:
        return None
    from evaluation.annotation import reference_for
    return reference_for(gold, key, question, answer)


def _context_evidence(context):
    content = context.get("chunk_content", context.get("content"))
    digest = context.get("chunk_sha256")
    full_characters = _number(context.get("content_characters"))
    truncated = bool(context.get("content_truncated")) or (
        full_characters is not None and isinstance(content, str) and full_characters > len(content))
    if not digest and isinstance(content, str) and content and not truncated:
        digest = hashlib.sha256(content.encode()).hexdigest()
    if not _valid_sha256(digest):
        digest = None
    return {
        "chunk_sha256": digest,
        "excerpt": content[:240] if isinstance(content, str) else None,
        "content_truncated": bool(context.get("content_truncated")) or
                             (isinstance(content, str) and len(content) > 240),
        "source_document": context.get("source_document"),
        "page_number": context.get("page_number"),
        "retrieval_scope": context.get("retrieval_scope", "case"),
        "chunk_index": context.get("chunk_index"),
        "rank": context.get("rank", context.get("chunk_rank")),
        "relevance_score": _number(context.get("relevance_score")),
    }


def _load(path, gold):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or not isinstance(obj.get("results"), list):
        raise ValueError(f"{Path(path).name}: expected ExperimentStore results array")
    source = obj.get("provenance") or obj.get("source") or {}
    source_path = obj.get("source_path") or source.get("source_path") or str(Path(path).name)
    family = obj.get("source_family") or source.get("source_family") or "unspecified"
    questions = {str(q.get("question_uuid")): q for q in obj.get("questions", [])}
    answers = {_key(a): a.get("answer_text") for a in obj.get("answers", [])}
    contexts = defaultdict(list)
    corrections = defaultdict(list)
    for context in obj.get("rag_contexts", []):
        contexts[_key(context)].append(_context_evidence(context))
    for correction in obj.get("corrections", []):
        corrections[_key(correction)].append(correction)
    records, seen = [], set()
    for result in obj["results"]:
        key = _key(result)
        if key in seen:
            raise ValueError(f"{Path(path).name}: duplicate question/student result")
        seen.add(key)
        question = questions.get(key[0], {})
        answer = answers.get(key)
        scores = [_number(result.get(n)) for n in ("c1_score", "c2_score", "final_score")]
        c1, c2, final = scores
        arbiter = _number(result.get("arbiter_score"))
        flags = []
        maximum = _number(question.get("total_points", question.get("max_score")))
        # Historical grader scores are on the documented 0-10 scale.
        maximum = maximum if maximum is not None else 10.0
        valid = all(s is not None and 0 <= s <= maximum for s in scores)
        if not valid:
            flags.append("invalid_or_missing_score")
        if arbiter is not None and not 0 <= arbiter <= maximum:
            arbiter = None
            flags.append("invalid_arbiter_score")
        metadata = result.get("processing_metadata") or {}
        ref = _reference(gold, key, question, answer)
        if ref is None:
            flags.append("no_verified_human_reference")
        material = _material(question, answer)
        if material is None:
            flags.append("incomplete_material_evidence")
        if valid and abs(c1 - c2) > 1:
            flags.append("high_examiner_disagreement")
        if obj.get("config", {}).get("rag_enabled") is True and not any(
                c["chunk_sha256"] and c["excerpt"] for c in contexts[key]):
            flags.append("retrieval_evidence_missing")
        if valid:
            expected = _consensus(c1, c2, arbiter) if arbiter is not None else (c1 + c2) / 2
            if abs(expected - final) > 0.011:
                flags.append("stored_consensus_differs_from_current_rule")
        records.append({
            "case_id": _case_id(key), "source": Path(path).name,
            "source_path": source_path, "source_family": family,
            "experiment_id": str(obj.get("id", Path(path).stem)),
            "synthetic": obj.get("data_origin") == "synthetic" or
                         obj.get("config", {}).get("data_origin") == "synthetic",
            "material_sha256": material, "question_sha256": _digest(question.get("statement"))
                if isinstance(question.get("statement"), str) else None,
            "answer_sha256": hashlib.sha256(answer.encode()).hexdigest()
                if isinstance(answer, str) else None,
            "rubric_sha256": _digest(_rubric(question)) if _rubric(question) is not None else None,
            "c1_score": c1, "c2_score": c2, "final_score": final, "arbiter_score": arbiter,
            "divergence": round(abs(c1 - c2), 6) if valid else None,
            "valid_scores": valid, "reference_score": ref,
            "retrieved_contexts": contexts[key], "flags": flags,
            "observed_total_latency_ms": _measurement(metadata.get("total_elapsed_ms")),
            "observed_total_cost_usd": _measurement(metadata.get("cost_usd")),
            "observed_arbiter_latency_ms": _measurement(metadata.get("arbiter_elapsed_ms")),
            "observed_arbiter_cost_usd": _measurement(metadata.get("arbiter_cost_usd")),
            "observed_retrieval_latency_ms": _measurement(metadata.get("retrieval_elapsed_ms")),
        })
    return {"name": Path(path).name, "source_path": source_path, "source_family": family,
            "config": obj.get("config") or {}, "records": records,
            "status": obj.get("config", {}).get("final_status") or obj.get("status"),
            "declared_export_status": obj.get("status"),
            "data_origin": obj.get("data_origin"), "response_origin": obj.get("response_origin")}


def arbitration_analysis(records, thresholds):
    eligible = [r for r in records if r["valid_scores"]]
    observed = []
    for record in eligible:
        if record["arbiter_score"] is None:
            continue
        baseline = (record["c1_score"] + record["c2_score"]) / 2
        reference = record["reference_score"]
        observed.append({
            "source": record["source"], "case_id": record["case_id"],
            "mean_2_score": baseline, "observed_final_score": record["final_score"],
            "arbiter_score": record["arbiter_score"],
            "score_shift": round(record["final_score"] - baseline, 6),
            "mean_2_absolute_error": abs(baseline - reference) if reference is not None else None,
            "final_absolute_error": abs(record["final_score"] - reference) if reference is not None else None,
            "arbiter_latency_ms": record["observed_arbiter_latency_ms"],
            "arbiter_cost_usd": record["observed_arbiter_cost_usd"],
        })
    labelled = [r for r in observed if r["final_absolute_error"] is not None]
    policies = []
    for threshold in thresholds:
        threshold = _number(threshold)
        if threshold is None or threshold < 0:
            raise ValueError("Arbitration thresholds must be finite non-negative numbers")
        outcomes, missing, triggered = [], [], []
        for record in eligible:
            call = record["divergence"] > threshold  # Same strict comparator as grader.
            baseline = (record["c1_score"] + record["c2_score"]) / 2
            if call:
                triggered.append(record)
                if record["arbiter_score"] is None:
                    missing.append({"source": record["source"], "case_id": record["case_id"]})
                    continue
                score = _consensus(record["c1_score"], record["c2_score"], record["arbiter_score"])
            else:
                score = baseline
            outcomes.append({"source": record["source"], "case_id": record["case_id"],
                             "score": round(score, 6), "score_shift": round(score - baseline, 6),
                             "stored_final_score": record["final_score"],
                             "matches_stored_final": abs(score - record["final_score"]) <= 0.011,
                             "reference_score": record["reference_score"],
                             "absolute_error": abs(score - record["reference_score"])
                             if record["reference_score"] is not None else None})
        complete = len(outcomes) == len(eligible) and bool(eligible)
        labels_complete = complete and all(r["absolute_error"] is not None for r in outcomes)
        latencies = [r["observed_arbiter_latency_ms"] for r in triggered]
        costs = [r["observed_arbiter_cost_usd"] for r in triggered]
        policies.append({
            "threshold": threshold, "comparison": "absolute_difference > threshold",
            "kind": "counterfactual_call_count_and_observed_score_replay",
            "eligible_rows": len(eligible), "would_trigger": len(triggered),
            "observed_arbiter_available": len(triggered) - len(missing),
            "outcomes_available": len(outcomes), "complete_policy_outcomes": complete,
            "replayed_vs_stored_final_mismatches": sum(not r["matches_stored_final"] for r in outcomes),
            "mean_absolute_score_shift": _mean([abs(r["score_shift"]) for r in outcomes]) if complete else None,
            "reference_mae": _mean([r["absolute_error"] for r in outcomes]) if labels_complete else None,
            "mean_observed_arbiter_latency_ms": _mean(latencies)
                if latencies and all(v is not None and v >= 0 for v in latencies) else None,
            "total_observed_arbiter_cost_usd": round(sum(costs), 8)
                if costs and all(v is not None and v >= 0 for v in costs) else None,
            "missing_arbiter_cases": missing, "replayed_outcomes": outcomes,
            "limitation": "Reuses only observed arbiter scores; no new calls or unobserved outcomes. "
                          "Policy replay does not measure accuracy or causally identify arbiter quality.",
        })
    return {
        "eligible_rows": len(eligible), "observed_arbiter_rows": len(observed),
        "mean_absolute_observed_score_shift": _mean([abs(r["score_shift"]) for r in observed]),
        "observed_outcomes": observed,
        "reference_comparison": {"n": len(labelled),
            "mean_2_mae": _mean([r["mean_2_absolute_error"] for r in labelled]),
            "observed_final_mae": _mean([r["final_absolute_error"] for r in labelled]),
            "design": "same observed cases; selected by historical policy, not randomized"} if labelled else None,
        "threshold_simulation": policies,
        "limitation": "Repeated historical rows are not independent learners. Arbitration was selected "
                      "by disagreement; grade movement is not evidence of improved correctness.",
    }


_PAIR_NAMES = (
    ("experiment_A_pareado_3.json", "experiment_B_pareado_4.json", "tcc_paired"),
    ("experiment_A_final_6.json", "experiment_B_final_7.json", "tcc_final"),
    ("experiment_A_v3_13.json", "experiment_B_v3_14.json", "tcc_v3"),
    ("experiment_A_7.json", "experiment_B_8.json", "tcc_backend_timeouts"),
    ("cond_A_20260328_163833.json", "cond_B_20260328_163833.json", "notebook_ab"),
)


def _pair_sources(exports):
    pairs, used = [], set()
    for a_name, b_name, label in _PAIR_NAMES:
        a = [e for e in exports if Path(e["source_path"]).name == a_name]
        b = [e for e in exports if Path(e["source_path"]).name == b_name]
        if len(a) == len(b) == 1:
            pairs.append((label, a[0], b[0]))
            used.update((a[0]["name"], b[0]["name"]))
    by_id = defaultdict(list)
    for export in exports:
        comparison = export["config"].get("comparison_id")
        if comparison and export["name"] not in used:
            by_id[str(comparison)].append(export)
    for comparison, group in sorted(by_id.items()):
        a = [e for e in group if e["config"].get("rag_enabled") is True]
        b = [e for e in group if e["config"].get("rag_enabled") is False]
        if len(a) == len(b) == 1:
            pairs.append((comparison, a[0], b[0]))
            used.update((a[0]["name"], b[0]["name"]))
    return pairs, [e["name"] for e in exports if e["name"] not in used and
                   e["config"].get("rag_enabled") in (True, False)]


def _configuration_blockers(rag, no_rag, *, arbitration_used=False):
    reasons = []
    for field in ("llm_provider", "llm_model", "llm_temperature", "divergence_threshold"):
        a, b = rag.get(field), no_rag.get(field)
        if a is None or b is None:
            reasons.append("unknown_configuration:" + field)
        elif a != b:
            reasons.append("configuration_mismatch:" + field)
    fingerprint_fields = ["examiner_prompt_file_sha256", "examiner_runtime_file_sha256",
                          "workflow_file_sha256", "consensus_runtime_file_sha256"]
    if arbitration_used:
        fingerprint_fields.append("arbiter_runtime_file_sha256")
    for field in fingerprint_fields:
        a = (rag.get("source_fingerprints") or {}).get(field)
        b = (no_rag.get("source_fingerprints") or {}).get(field)
        if not _valid_sha256(a) or not _valid_sha256(b):
            reasons.append("unknown_configuration:" + field)
        elif a != b:
            reasons.append("configuration_mismatch:" + field)
    if rag.get("rag_enabled") is not True or no_rag.get("rag_enabled") is not False:
        reasons.append("rag_treatment_not_verified")
    for field in ("embedding_provider", "embedding_model", "rag_top_k"):
        if rag.get(field) is None:
            reasons.append("unknown_retrieval_configuration:" + field)
    if not _valid_sha256((rag.get("source_fingerprints") or {}).get("retriever_file_sha256")):
        reasons.append("unknown_retrieval_configuration:retriever_file_sha256")
    return reasons


def rag_analysis(exports):
    source_pairs, unpaired = _pair_sources(exports)
    comparisons = []
    for label, rag, no_rag in source_pairs:
        rag_records = [r for r in rag["records"] if r["valid_scores"]]
        no_rag_records = [r for r in no_rag["records"] if r["valid_scores"]]
        a_index, b_index = defaultdict(list), defaultdict(list)
        for record in rag_records:
            if record["material_sha256"]:
                a_index[record["material_sha256"]].append(record)
        for record in no_rag_records:
            if record["material_sha256"]:
                b_index[record["material_sha256"]].append(record)
        config_reasons = _configuration_blockers(rag["config"], no_rag["config"],
            arbitration_used=any(r["arbiter_score"] is not None for r in rag_records + no_rag_records))
        pairs, matched_a, matched_b = [], set(), set()
        for material in sorted(a_index.keys() & b_index.keys()):
            a_rows, b_rows = a_index[material], b_index[material]
            if len(a_rows) != 1 or len(b_rows) != 1:
                # Do not create Cartesian pairs or silently choose an observation.
                continue
            a, b = a_rows[0], b_rows[0]
            matched_a.add(a["case_id"])
            matched_b.add(b["case_id"])
            reasons = list(config_reasons)
            if not any(c["chunk_sha256"] and c["excerpt"] for c in a["retrieved_contexts"]):
                reasons.append("retrieval_evidence_missing")
            if b["retrieved_contexts"]:
                reasons.append("no_rag_arm_has_retrieved_contexts")
            if a["synthetic"] != b["synthetic"]:
                reasons.append("mixed_synthetic_and_historical_arms")
            a_ref, b_ref = a["reference_score"], b["reference_score"]
            if a_ref is not None and b_ref is not None and a_ref != b_ref:
                reasons.append("inconsistent_reference_for_identical_material")
            reference = a_ref if a_ref is not None and a_ref == b_ref else None
            latency_a, latency_b = a["observed_total_latency_ms"], b["observed_total_latency_ms"]
            cost_a, cost_b = a["observed_total_cost_usd"], b["observed_total_cost_usd"]
            pairs.append({
                "material_sha256": material, "rag_case_id": a["case_id"],
                "no_rag_case_id": b["case_id"], "rag_final_score": a["final_score"],
                "no_rag_final_score": b["final_score"],
                "score_delta": round(a["final_score"] - b["final_score"], 6),
                "divergence_delta": round(a["divergence"] - b["divergence"], 6),
                "retrieved_contexts": a["retrieved_contexts"],
                "eligible_controlled_comparison": not reasons,
                "blocking_reasons": sorted(set(reasons)),
                "reference_absolute_error_delta": round(abs(a["final_score"] - reference) -
                                                          abs(b["final_score"] - reference), 6)
                    if reference is not None and not reasons else None,
                "observed_latency_delta_ms": round(latency_a - latency_b, 6)
                    if latency_a is not None and latency_b is not None else None,
                "observed_cost_delta_usd": round(cost_a - cost_b, 8)
                    if cost_a is not None and cost_b is not None else None,
                "flags": sorted(set(a["flags"] + b["flags"])),
            })
        unmatched = []
        for arm, rows, matched, opposite in (("rag", rag_records, matched_a, b_index),
                                              ("no_rag", no_rag_records, matched_b, a_index)):
            for record in rows:
                if record["case_id"] in matched:
                    continue
                material = record["material_sha256"]
                reason = "incomplete_material_evidence" if not material else (
                    "ambiguous_duplicate_material" if material in opposite else "no_exact_material_match")
                unmatched.append({"arm": arm, "case_id": record["case_id"], "reason": reason})
        eligible = [p for p in pairs if p["eligible_controlled_comparison"]]
        reference_pairs = [p for p in eligible if p["reference_absolute_error_delta"] is not None]
        comparisons.append({
            "comparison_id": label, "source_rag": rag["source_path"],
            "source_no_rag": no_rag["source_path"],
            "source_status": {"rag": rag["status"], "no_rag": no_rag["status"]},
            "rag_rows": len(rag_records), "no_rag_rows": len(no_rag_records),
            "exact_material_pairs": len(pairs), "eligible_controlled_pairs": len(eligible),
            "mean_score_shift_descriptive": _mean([p["score_delta"] for p in pairs]),
            "mean_divergence_shift_descriptive": _mean([p["divergence_delta"] for p in pairs]),
            "controlled_mean_score_shift": _mean([p["score_delta"] for p in eligible]),
            "reference_effect": {"n": len(reference_pairs),
                "mean_absolute_error_delta_rag_minus_no_rag": _mean(
                    [p["reference_absolute_error_delta"] for p in reference_pairs])}
                if reference_pairs else None,
            "configuration_blocking_reasons": config_reasons,
            "pairs": pairs, "unmatched_cases": unmatched,
            "interpretation": "Exact material pairing controls question, rubric, answer and scale. "
                "Missing setup or retrieval evidence blocks a controlled interpretation. "
                "A score shift without verified human references does not measure quality. "
                "Even eligible historical pairs are observational; causal claims require a preregistered "
                "randomized/repeated design and an independent reference.",
        })
    coverage = []
    for export in exports:
        contexts = [c for r in export["records"] for c in r["retrieved_contexts"]]
        unique = {c["chunk_sha256"]: c for c in contexts if c["chunk_sha256"]}
        coverage.append({"source": export["name"], "source_family": export["source_family"],
                         "rows": len(export["records"]),
                         "rag_enabled": export["config"].get("rag_enabled"),
                         "rows_with_context_content": sum(any(c["chunk_sha256"] and c["excerpt"]
                             for c in r["retrieved_contexts"]) for r in export["records"]),
                         "context_assignments": len(contexts), "unique_content_hashes": len(unique),
                         "context_examples": [unique[h] for h in sorted(unique)[:3]]})
    return {"comparisons": comparisons, "unpaired_sources": unpaired,
            "retrieval_coverage": coverage,
            "causal_quality_effect": None,
            "limitation": "Historical exports do not establish randomized treatment allocation. "
                          "Relevance scores and textbook excerpts are retrieval traces, not human relevance judgments."}


def evaluate_experiments(paths, gold=None, thresholds=(0.5, 1.0, 1.5, 2.0)):
    exports = [_load(path, gold) for path in sorted(map(str, paths))]
    records = [record for export in exports for record in export["records"]]
    origins = {r["synthetic"] for r in records}
    if len(origins) > 1:
        raise ValueError("Synthetic and historical exports must be evaluated separately")
    synthetic = bool(records) and origins == {True}
    by_family = defaultdict(list)
    for export in exports:
        by_family[export["source_family"]].append(export)
    per_family = []
    for family, family_exports in sorted(by_family.items()):
        family_records = [r for export in family_exports for r in export["records"]]
        analysis = arbitration_analysis(family_records, thresholds)
        per_family.append({"source_family": family,
                           "sources": [e["name"] for e in family_exports],
                           "source_status": {e["name"]: e["status"] for e in family_exports},
                           "eligible_rows": analysis["eligible_rows"],
                           "observed_arbiter_rows": analysis["observed_arbiter_rows"],
                           "mean_absolute_observed_score_shift": analysis["mean_absolute_observed_score_shift"],
                           "threshold_simulation": [{k: v for k, v in policy.items()
                               if k not in {"replayed_outcomes", "missing_arbiter_cases"}}
                               for policy in analysis["threshold_simulation"]]})
    return {
        "schema_version": 1, "report_type": "arbitration_and_rag",
        "data_origin": "synthetic_demonstration" if synthetic else "historical_exports",
        "sources": [{"source": e["name"], "source_path": e["source_path"],
                     "source_family": e["source_family"], "rows": len(e["records"]),
                     "response_origin": e["response_origin"],
                     "declared_export_status": e["declared_export_status"],
                     "status": e["status"]} for e in exports],
        "arbitration": arbitration_analysis(records, thresholds),
        "arbitration_by_source_family": per_family,
        "rag": rag_analysis(exports),
        "failures": [{"source": r["source"], "case_id": r["case_id"], "flags": r["flags"]}
                     for r in records if r["flags"]],
        "source_failures": [{"source": e["name"], "status": e["status"],
                             "declared_export_status": e["declared_export_status"],
                             "flags": ["no_recorded_outcomes"] +
                                      (["export_status_conflicts_with_execution_status"]
                                       if e["declared_export_status"] == "completed" and
                                          e["status"] != "completed" else [])}
                            for e in exports if not e["records"]],
        "measurement_policy": "Null means not measured or not identifiable. No API calls, "
                              "human labels, costs, or latencies are fabricated. "
                              "Synthetic outputs demonstrate software behavior only.",
    }


def write_outputs(report, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "experiments.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                                encoding="utf-8")
    rows = report["arbitration"]["observed_outcomes"]
    if rows:
        with (directory / "arbitration_observed.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    elif (directory / "arbitration_observed.csv").exists():
        (directory / "arbitration_observed.csv").unlink()
    rows = []
    for comparison in report["rag"]["comparisons"]:
        for pair in comparison["pairs"]:
            rows.append({"comparison_id": comparison["comparison_id"],
                         **{k: v for k, v in pair.items() if k not in {"retrieved_contexts", "flags"}},
                         "blocking_reasons": "|".join(pair["blocking_reasons"]),
                         "retrieved_context_count": len(pair["retrieved_contexts"])})
    if rows:
        with (directory / "rag_pairs.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    elif (directory / "rag_pairs.csv").exists():
        (directory / "rag_pairs.csv").unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exports", nargs="+", help="Deidentified ExperimentStore JSON exports")
    parser.add_argument("--gold", help="Verified, adjudicated human annotation file")
    parser.add_argument("--output", default="evaluation/data")
    args = parser.parse_args()
    gold = None
    if args.gold:
        from evaluation.annotation import load_gold
        gold = load_gold(args.gold)
    report = evaluate_experiments(args.exports, gold=gold)
    write_outputs(report, args.output)
    print(json.dumps({"data_origin": report["data_origin"],
                      "rows": report["arbitration"]["eligible_rows"],
                      "observed_arbiters": report["arbitration"]["observed_arbiter_rows"],
                      "rag_comparisons": len(report["rag"]["comparisons"]),
                      "output": str(Path(args.output) / "experiments.json")}))


if __name__ == "__main__":
    main()
