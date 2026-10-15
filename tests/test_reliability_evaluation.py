"""Offline reliability evaluation unit tests (standard library only)."""
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.reliability import agreement_metrics, evaluate_exports, load_gold, write_outputs
from evaluation.annotation import annotation_template, make_packet, material_hash


def _experiment(condition="QA4 R1/2", answer="same answer", score=5.0, c1=4.0, c2=6.0,
                contexts=None, include_answer=True, model="test-model"):
    return {
        "id": int(condition[-3]) if condition.startswith("QA4 R") else 1,
        "config": {
            "condition": condition, "llm_provider": "test", "llm_model": model,
            "llm_temperature": 0, "rag_enabled": True, "rag_top_k": 4,
        },
        "questions": [{"question_uuid": "q1", "statement": "Test question", "total_points": 10.0,
                       "rubric_json": [{"name": "accuracy", "weight": 1.0, "max_score": 10.0}]}],
        "students": [{"student_id": "s1", "quality_profile": "poor"}],
        "answers": [{"question_uuid": "q1", "student_id": "s1", "answer_text": answer}] if include_answer else [],
        "rag_contexts": contexts if contexts is not None else [
            {"question_uuid": "q1", "student_id": "s1", "chunk_content": "reference text"}
        ],
        "corrections": [
            {"question_uuid": "q1", "student_id": "s1",
             "agent_role": "corretor_1", "criterion_scores": [{"criterion": "accuracy", "score": 4}]}
        ],
        "results": [{
            "question_uuid": "q1", "student_id": "s1",
            "c1_score": c1, "c2_score": c2, "final_score": score, "arbiter_score": None,
        }],
    }


class ReliabilityEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, name, obj):
        path = self.root / name
        path.write_text(json.dumps(obj), encoding="utf-8")
        return path

    def test_qa4_stability_and_strict_threshold(self):
        a = self.put("a.json", _experiment(score=5.0))
        b = self.put("b.json", _experiment(condition="QA4 R2/2", score=5.6, c1=5.2, c2=6.0))
        report = evaluate_exports([a, b])
        self.assertEqual(report["total_corrections"], 2)
        self.assertEqual(report["stability"][0]["score_range"], 0.6)
        self.assertTrue(report["stability"][0]["verified_identical_answer"])
        self.assertEqual(report["threshold_simulation"][3]["would_trigger"], 0)
        self.assertEqual(report["threshold_simulation"][1]["would_trigger"], 1)

    def test_changed_answers_not_compared_for_stability(self):
        a = self.put("a.json", _experiment())
        b = self.put("b.json", _experiment(condition="QA4 R2/2", answer="different answer"))
        report = evaluate_exports([a, b])
        self.assertEqual(report["stability"], [])
        self.assertTrue(any("answer text changed" in w for w in report["warnings"]))

    def test_missing_answers_only_descriptive(self):
        a = self.put("a.json", _experiment(include_answer=False))
        b = self.put("b.json", _experiment(condition="QA4 R2/2", include_answer=False))
        report = evaluate_exports([a, b])
        self.assertFalse(report["stability"][0]["verified_identical_answer"])
        self.assertTrue(any("descriptive only" in w for w in report["warnings"]))

    def test_model_change_prevents_cross_config_stability(self):
        a = self.put("a.json", _experiment())
        b = self.put("b.json", _experiment(condition="QA4 R2/2", model="model-v2"))
        self.assertEqual(evaluate_exports([a, b])["stability"], [])

    def test_missing_rag_evidence_not_claimed_as_effect(self):
        a = self.put("a.json", _experiment(contexts=[]))
        report = evaluate_exports([a])
        self.assertIn("retrieval_evidence_missing", report["records"][0]["flags"])
        self.assertTrue(any("do not infer RAG impact" in w for w in report["warnings"]))

    def gold(self, export, reference_score=4.0):
        """Unit-test provenance declarations; these are never research labels."""
        packet = make_packet([export], "unit-test-fixture")
        obj = annotation_template(packet)
        item = obj["items"][0]
        item.update(review_status="adjudicated", reference_score=reference_score)
        criterion_scores = [{"criterion": "accuracy", "score": reference_score, "max_score": 10.0}]
        item["independent_ratings"] = [
            {"reviewer_id": reviewer, "score": reference_score, "blinded_to_model_scores": True,
             "material_sha256": item["material_sha256"], "rationale": "Unit test only",
             "recorded_at": "2026-01-01T00:00:00Z", "criterion_scores": criterion_scores}
            for reviewer in ("unit-test-A", "unit-test-B")]
        item["adjudication"] = {"reviewer_id": "unit-test-A", "rationale": "Unit test only",
                                "recorded_at": "2026-01-01T00:00:00Z", "criterion_scores": criterion_scores,
                                "material_sha256": item["material_sha256"]}
        return obj

    def test_evidence_checked_gold_only(self):
        experiment = _experiment()
        a = self.put("a.json", experiment)
        gold = self.gold(experiment)
        gold["items"].append({"review_status": "draft"})
        report = evaluate_exports([a], gold=load_gold(self.put("gold.json", gold)))
        self.assertEqual(report["reference_metrics"]["mae"], 1.0)
        self.assertEqual(report["reference_metrics"]["rmse"], 1.0)
        self.assertEqual(report["reference_metrics"]["bias"], 1.0)
        write_outputs(report, self.root / "out")
        self.assertTrue((self.root / "out" / "corrections.csv").is_file())

    def test_gold_does_not_match_changed_material(self):
        e = _experiment()
        labels = load_gold(self.put("gold.json", self.gold(e)))
        e["answers"][0]["answer_text"] = "Changed after annotation"
        report = evaluate_exports([self.put("changed.json", e)], gold=labels)
        self.assertIsNone(report["reference_metrics"])
        self.assertTrue(any("reference excluded" in warning for warning in report["warnings"]))

    def test_plain_mapping_does_not_bypass_human_evidence(self):
        with self.assertRaisesRegex(ValueError, "validated human"):
            evaluate_exports([self.put("a.json", _experiment())], gold={("q1", "s1"): 5.0})

    def test_agreement_detects_shift_despite_perfect_correlation(self):
        metrics = agreement_metrics([(1, 2), (3, 4), (5, 6)])
        self.assertEqual(metrics["pearson_r"], 1.0)
        self.assertLess(metrics["lin_concordance"], 1.0)
        self.assertEqual(metrics["mean_absolute_difference"], 1.0)
        self.assertEqual(metrics["signed_difference_c1_minus_c2"], -1.0)
        self.assertEqual(metrics["within_1_0_rate"], 1.0)
        self.assertIsNone(agreement_metrics([(0, 0), (0, 0)])["pearson_r"])
        self.assertIsNone(agreement_metrics([])["mean_absolute_difference"])

    def test_exports_inconsistent_metadata_are_flagged_not_repaired(self):
        experiment = _experiment(score=9.88, c1=9.8, c2=9.88)
        experiment["results"][0]["divergence_value"] = 0.2
        report = evaluate_exports([self.put("inconsistent.json", experiment)])
        row = report["records"][0]
        self.assertEqual(row["divergence"], 0.08)
        self.assertIn("exported_divergence_inconsistent", row["flags"])
        self.assertIn("consensus_score_inconsistent", row["flags"])
        self.assertEqual(row["final_score"], 9.88)

    def test_question_or_rubric_change_excluded_from_stability(self):
        a = _experiment()
        b = _experiment(condition="QA4 R2/2")
        b["questions"][0]["statement"] = "Different question"
        self.assertEqual(evaluate_exports([self.put("a.json", a), self.put("b.json", b)])["stability"], [])

    def test_known_changed_answer_excluded_even_if_third_answer_is_missing(self):
        paths = [self.put("a.json", _experiment()),
                 self.put("b.json", _experiment(condition="QA4 R2/3", answer="changed")),
                 self.put("c.json", _experiment(condition="QA4 R3/3", include_answer=False))]
        self.assertEqual(evaluate_exports(paths)["stability"], [])

    def test_different_source_families_are_never_grouped_for_stability(self):
        a = _experiment()
        b = _experiment(condition="QA4 R2/2")
        a["provenance"] = {"source_family": "cohort_A"}
        b["provenance"] = {"source_family": "cohort_B"}
        self.assertEqual(evaluate_exports([self.put("a.json", a), self.put("b.json", b)])["stability"], [])

    def test_identical_material_does_not_imply_complete_configuration(self):
        report = evaluate_exports([self.put("a.json", _experiment()),
                                   self.put("b.json", _experiment(condition="QA4 R2/2"))])
        self.assertTrue(report["stability"][0]["verified_identical_material"])
        self.assertFalse(report["stability"][0]["verified_complete_configuration"])

    def test_invalid_threshold_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_exports([], thresholds=[float("nan")])

    def test_duplicate_result_is_rejected(self):
        e = _experiment()
        e["results"].append(dict(e["results"][0]))
        a = self.put("a.json", e)
        with self.assertRaisesRegex(ValueError, "duplicate question/student"):
            evaluate_exports([a])

    def test_invalid_gold_is_rejected(self):
        obj = self.gold(_experiment())
        obj["items"][0]["reference_score"] = 11
        with self.assertRaisesRegex(ValueError, "reference_score"):
            load_gold(self.put("gold.json", obj))


if __name__ == "__main__":
    unittest.main()
