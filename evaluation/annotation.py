"""Blind annotation packets and evidence-checked reference-label import.

A schema declaration cannot establish that a person actually graded an answer. This
module verifies the recorded provenance and material identity; research owners must
retain reviewer consent/qualification and independent-rating evidence privately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def rubric_for(question):
    rubric = question.get("rubric_json", question.get("rubric", []))
    if isinstance(rubric, str):
        try:
            rubric = json.loads(rubric)
        except json.JSONDecodeError as exc:
            raise ValueError("Question rubric_json is invalid JSON") from exc
    return rubric


def material_hash(question, answer):
    """Fingerprint complete, valid material; never assume a missing scale/rubric."""
    statement = question.get("statement")
    points = question.get("total_points")
    if not isinstance(answer, str) or not answer.strip() or not isinstance(statement, str) or not statement.strip():
        return None
    if isinstance(points, bool) or not isinstance(points, (int, float)) or not math.isfinite(points) or points <= 0:
        return None
    try:
        rubric = rubric_for(question)
    except ValueError:
        return None
    if not isinstance(rubric, list) or not rubric:
        return None
    names, weights = set(), []
    for criterion in rubric:
        if not isinstance(criterion, dict):
            return None
        name, weight, maximum = criterion.get("name"), criterion.get("weight"), criterion.get("max_score")
        if not isinstance(name, str) or not name.strip() or name in names:
            return None
        if any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n)
               for n in (weight, maximum)) or weight < 0 or maximum <= 0:
            return None
        names.add(name)
        weights.append(weight)
    if abs(sum(weights) - 1.0) > 1e-6:
        return None
    return canonical_hash({"statement": statement, "rubric": rubric,
                           "total_points": points, "answer_text": answer})


class GoldLabels(dict):
    """Validated references, with a material fingerprint for each labelled case."""
    def __init__(self, *, origin="human", provenance=None):
        super().__init__()
        self.origin = origin
        self.provenance = provenance or {}
        self.material_hashes = {}
        self.by_material = {}
        self.items_by_material = {}


def _score(value, label="score"):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number between 0 and 10")
    if not math.isfinite(value) or not 0 <= value <= 10:
        raise ValueError(f"{label} must be a finite number between 0 and 10")
    return float(value)


def _criterion_scores(rows, label):
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{label} criterion_scores are required")
    seen = set()
    for row in rows:
        name = _nonempty(row.get("criterion"), f"{label} criterion name")
        if name in seen:
            raise ValueError(f"{label} duplicate criterion")
        seen.add(name)
        score = row.get("score")
        maximum = row.get("max_score")
        if isinstance(score, bool) or isinstance(maximum, bool) or not isinstance(score, (int, float)) or not isinstance(maximum, (int, float)):
            raise ValueError(f"{label} criterion score/max_score must be numeric")
        if not math.isfinite(score) or not math.isfinite(maximum) or maximum <= 0 or not 0 <= score <= maximum:
            raise ValueError(f"{label} criterion score must be within its declared scale")


def _nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    return value


def validate_gold(obj, *, allow_synthetic=False):
    if obj.get("schema_version") != 2 or not isinstance(obj.get("items"), list):
        raise ValueError("Gold file requires schema_version=2 and items array; legacy labels lack provenance")
    origin = obj.get("label_origin")
    if origin != "human" and not (allow_synthetic and origin == "synthetic_demo"):
        raise ValueError("Only recorded human labels can enter research metrics; synthetic demo requires explicit opt-in")
    provenance = obj.get("provenance") or {}
    for field in ("dataset_id", "annotation_protocol", "source_attribution"):
        _nonempty(provenance.get(field), f"provenance.{field}")
    labels = GoldLabels(origin=origin, provenance=provenance)
    for item in obj["items"]:
        if item.get("review_status") != "adjudicated":
            continue
        key = (_nonempty(item.get("question_uuid"), "question_uuid"),
               _nonempty(item.get("student_id"), "student_id"))
        digest = item.get("material_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Adjudicated label requires material_sha256")
        if (*key, digest) in labels.by_material:
            raise ValueError("Duplicate adjudicated label for case/material")
        ratings = item.get("independent_ratings")
        if not isinstance(ratings, list) or len(ratings) < 2:
            raise ValueError("At least two recorded independent ratings are required")
        reviewers = set()
        for rating in ratings:
            reviewer = _nonempty(rating.get("reviewer_id"), "reviewer_id")
            if reviewer in reviewers:
                raise ValueError("Independent reviewer IDs must be distinct")
            reviewers.add(reviewer)
            if rating.get("blinded_to_model_scores") is not True:
                raise ValueError("Independent ratings must attest blindness to model scores")
            if rating.get("material_sha256") != digest:
                raise ValueError("Reviewer material fingerprint mismatch")
            _score(rating.get("score"), "Independent rating score")
            _criterion_scores(rating.get("criterion_scores"), "Independent rating")
            _nonempty(rating.get("rationale"), "Independent rating rationale")
            _nonempty(rating.get("recorded_at"), "Independent rating recorded_at")
        adjudication = item.get("adjudication") or {}
        _nonempty(adjudication.get("reviewer_id"), "Adjudicator reviewer_id")
        _nonempty(adjudication.get("rationale"), "Adjudication rationale")
        _nonempty(adjudication.get("recorded_at"), "Adjudication recorded_at")
        _criterion_scores(adjudication.get("criterion_scores"), "Adjudication")
        if adjudication.get("material_sha256") != digest:
            raise ValueError("Adjudication material fingerprint mismatch")
        labels[key] = _score(item.get("reference_score"), "Adjudicated reference_score")
        labels.material_hashes.setdefault(key, set()).add(digest)
        labels.by_material[(*key, digest)] = labels[key]
        labels.items_by_material[(*key, digest)] = item
    return labels


def load_gold(path, *, allow_synthetic=False):
    if path is None:
        return GoldLabels()
    return validate_gold(json.loads(Path(path).read_text(encoding="utf-8")),
                         allow_synthetic=allow_synthetic)


def _validate_rubric_decisions(item, material):
    rubric = {row["name"]: row for row in material["rubric"]}
    if abs(sum(row["weight"] for row in rubric.values()) - 1.0) > 1e-6:
        raise ValueError("Annotation rubric weights must sum to one")
    decisions = [(rating, rating["score"]) for rating in item["independent_ratings"]]
    decisions.append((item["adjudication"], item["reference_score"]))
    for decision, total in decisions:
        scores = {row["criterion"]: row for row in decision["criterion_scores"]}
        if set(scores) != set(rubric):
            raise ValueError("Recorded criterion scores must cover the exact frozen rubric")
        if any(scores[name]["max_score"] != rule["max_score"] for name, rule in rubric.items()):
            raise ValueError("Criterion scoring scale does not match frozen rubric")
        weighted_total = sum(scores[name]["score"] / rule["max_score"] * rule["weight"]
                             for name, rule in rubric.items()) * material["total_points"]
        if abs(total - weighted_total) > 0.011:
            raise ValueError("Recorded total score does not match weighted criterion scores")


def reference_for(gold, key, question, answer):
    """Return a real reference only when its exact annotation material matches."""
    if not isinstance(gold, GoldLabels) or gold.origin != "human":
        return None
    key = tuple(str(x) for x in key)
    digest = material_hash(question or {}, answer)
    material_key = (*key, digest)
    if digest is None or material_key not in gold.by_material:
        return None
    try:
        _validate_rubric_decisions(gold.items_by_material[material_key],
                                  {"rubric": rubric_for(question),
                                   "total_points": question.get("total_points", 10.0)})
    except (ValueError, KeyError, TypeError, ZeroDivisionError):
        return None
    return gold.by_material[material_key]


def make_packet(exports, dataset_id="tcc-historical-v1"):
    cases = {}
    for obj in exports:
        questions = {str(q["question_uuid"]): q for q in obj.get("questions", [])}
        for answer in obj.get("answers", []):
            question = questions.get(str(answer.get("question_uuid")), {})
            text = answer.get("answer_text")
            digest = material_hash(question, text)
            if digest is None:
                continue
            key = (str(answer["question_uuid"]), str(answer["student_id"]), digest)
            # This is an annotation sampling unit, not a claim that QA4's absent
            # historic answer text can be reconstructed from another experiment.
            case_id = "annotation-" + canonical_hash(key)[:16]
            if key not in cases:
                cases[key] = {"case_id": case_id, "question_uuid": key[0], "student_id": key[1],
                              "material_sha256": digest, "statement": question["statement"],
                              "rubric": rubric_for(question), "total_points": question.get("total_points", 10.0),
                              "answer_text": text,
                              "split": "held_out" if int(canonical_hash(text)[:8], 16) % 4 == 0 else "development"}
    items = sorted(cases.values(), key=lambda item: item["case_id"])
    return {"schema_version": 1, "dataset_id": dataset_id,
            "status": "unlabelled_annotation_material", "label_origin": None,
            "blind_to": ["model_scores", "response_quality_profile", "experiment_condition"],
            "note": "No reviewers have been recruited or promised. No human reference labels are present.",
            "items": items}


def annotation_template(packet):
    return {"schema_version": 2, "label_origin": "human",
            "provenance": {"dataset_id": packet["dataset_id"],
                           "annotation_protocol": "evaluation/ANNOTATION_PROTOCOL.md",
                           "source_attribution": "Repository owner's public synthetic TCC responses; see evaluation/data/manifest.json source hashes"},
            "items": [{"case_id": item["case_id"], "question_uuid": item["question_uuid"],
                       "student_id": item["student_id"], "material_sha256": item["material_sha256"],
                       "review_status": "unreviewed", "reference_score": None,
                       "independent_ratings": [], "adjudication": None}
                      for item in packet["items"]]}


def import_annotations(packet, obj, *, allow_synthetic=False):
    if packet.get("schema_version") != 1 or not isinstance(packet.get("items"), list):
        raise ValueError("Frozen packet requires schema_version=1 and items array")
    _nonempty(packet.get("dataset_id"), "Packet dataset_id")
    seen_materials = set()
    for material in packet["items"]:
        digest = material_hash(material, material.get("answer_text"))
        if digest is None or digest != material.get("material_sha256"):
            raise ValueError("Frozen packet material fingerprint does not match its content")
        key = (_nonempty(material.get("question_uuid"), "Packet question_uuid"),
               _nonempty(material.get("student_id"), "Packet student_id"), digest)
        if key in seen_materials:
            raise ValueError("Frozen packet contains duplicate case/material")
        seen_materials.add(key)
    labels = validate_gold(obj, allow_synthetic=allow_synthetic)
    if labels.provenance["dataset_id"] != packet["dataset_id"]:
        raise ValueError("Annotation dataset does not match packet")
    expected = {(item["question_uuid"], item["student_id"], item["material_sha256"]): item
                for item in packet["items"]}
    for key in labels.by_material:
        if key not in expected:
            raise ValueError("Annotation case/material is absent from frozen packet")
    adjudicated = [item for item in obj["items"] if item.get("review_status") == "adjudicated"]
    for item in adjudicated:
        material = expected[(item["question_uuid"], item["student_id"], item["material_sha256"])]
        _validate_rubric_decisions(item, material)
    human_differences = [abs(item["independent_ratings"][0]["score"] - item["independent_ratings"][1]["score"])
                         for item in adjudicated]
    return {**obj, "import_validation": {"adjudicated_cases": len(labels.by_material),
            "recorded_reviewer_mean_absolute_difference":
                sum(human_differences) / len(human_differences) if human_differences else None,
            "origin": labels.origin, "evidence_note": "Recorded provenance validated; human identity/qualification must be audited privately"}}


def synthetic_demo():
    """An explicit fixture exercises annotation import, never research accuracy."""
    question = {"question_uuid": "demo-question", "statement": "What is 2 + 2?",
                "total_points": 10.0,
                "rubric_json": [{"name": "correctness", "weight": 1.0, "max_score": 10.0}]}
    export = {"questions": [question], "answers": [{"question_uuid": "demo-question",
              "student_id": "demo-response", "answer_text": "4"}]}
    packet = make_packet([export], "synthetic-demo-only")
    obj = annotation_template(packet)
    obj["label_origin"] = "synthetic_demo"
    obj["provenance"]["source_attribution"] = "Invented arithmetic fixture; no human reviewers or annotations"
    item = obj["items"][0]
    item.update(review_status="adjudicated", reference_score=10.0)
    item["independent_ratings"] = [{"reviewer_id": reviewer, "score": score,
        "blinded_to_model_scores": True, "material_sha256": item["material_sha256"],
        "rationale": "Synthetic fixture rating, not a human judgement", "recorded_at": "synthetic-fixture",
        "criterion_scores": [{"criterion": "correctness", "score": score, "max_score": 10.0}]}
        for reviewer, score in (("synthetic-rater-A", 10.0), ("synthetic-rater-B", 9.0))]
    item["adjudication"] = {"reviewer_id": "synthetic-adjudicator", "material_sha256": item["material_sha256"],
        "rationale": "Synthetic fixture decision, not a human judgement", "recorded_at": "synthetic-fixture",
        "criterion_scores": [{"criterion": "correctness", "score": 10.0, "max_score": 10.0}]}
    return packet, import_annotations(packet, obj, allow_synthetic=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    importer = commands.add_parser("import", help="Validate references against a frozen blind packet")
    importer.add_argument("--packet", required=True)
    importer.add_argument("--annotations", required=True)
    importer.add_argument("--output", required=True)
    demo = commands.add_parser("demo", help="Exercise the pipeline using explicitly synthetic annotations")
    demo.add_argument("--output", default="evaluation/output/synthetic-annotation-demo")
    args = parser.parse_args()
    if args.command == "import":
        packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
        obj = json.loads(Path(args.annotations).read_text(encoding="utf-8"))
        result = import_annotations(packet, obj)
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(result["import_validation"], indent=2))
    else:
        packet, result = synthetic_demo()
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        for name, obj in (("packet.json", packet), ("synthetic_annotations.json", result)):
            (output / name).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
        print("Synthetic annotation import passed; 0 human references; research accuracy remains unavailable")


if __name__ == "__main__":
    main()
