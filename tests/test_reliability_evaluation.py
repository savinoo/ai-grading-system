"""Offline reliability evaluation unit tests (standard library only)."""
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.reliability import evaluate_exports, load_gold, write_outputs


def _experiment(condition="QA4 R1/2", answer="same answer", score=5.0, c1=4.0, c2=6.0,
                contexts=None, include_answer=True, model="test-model"):
    return {
        "id": int(condition[-3]) if condition.startswith("QA4 R") else 1,
        "config": {
            "condition": condition, "llm_provider": "test", "llm_model": model,
            "llm_temperature": 0, "rag_enabled": True, "rag_top_k": 4,
        },
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

    def test_adjudicated_gold_only(self):
        a = self.put("a.json", _experiment())
        gold_file = self.put("gold.json", {
            "schema_version": 1,
            "items": [
                {"question_uuid": "q1", "student_id": "s1",
                 "reference_score": 4.0, "review_status": "adjudicated"},
                {"question_uuid": "q2", "student_id": "s2",
                 "reference_score": 8.0, "review_status": "draft"},
            ]
        })
        report = evaluate_exports([a], gold=load_gold(gold_file))
        self.assertEqual(report["reference_metrics"]["mae"], 1.0)
        self.assertEqual(report["reference_metrics"]["rmse"], 1.0)
        self.assertEqual(report["reference_metrics"]["bias"], 1.0)
        write_outputs(report, self.root / "out")
        self.assertTrue((self.root / "out" / "corrections.csv").is_file())

    def test_duplicate_result_is_rejected(self):
        e = _experiment()
        e["results"].append(dict(e["results"][0]))
        a = self.put("a.json", e)
        with self.assertRaisesRegex(ValueError, "duplicate question/student"):
            evaluate_exports([a])

    def test_invalid_gold_is_rejected(self):
        path = self.put("gold.json", {
            "schema_version": 1, "items": [
                {"question_uuid": "q1", "student_id": "s1",
                 "reference_score": 11, "review_status": "adjudicated"}
            ]
        })
        with self.assertRaises(ValueError):
            load_gold(path)


if __name__ == "__main__":
    unittest.main()
