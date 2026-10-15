"""Evidence gates for historical arbitration/RAG; all material here is synthetic."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.experiments import evaluate_experiments


def synthetic_export(rag=True):
    config = {
        "data_origin": "synthetic", "comparison_id": "synthetic_controlled_demo",
        "rag_enabled": rag, "llm_provider": "synthetic_no_provider",
        "llm_model": "synthetic_no_model", "llm_temperature": 0,
        "divergence_threshold": 2, "embedding_provider": "synthetic_no_provider",
        "embedding_model": "synthetic_no_model", "rag_top_k": 1,
        "source_fingerprints": {name + "_file_sha256": "0" * 64 for name in
                                ("examiner_prompt", "examiner_runtime", "workflow", "retriever",
                                 "arbiter_runtime", "consensus_runtime")},
    }
    return {
        "id": "synthetic_rag" if rag else "synthetic_no_rag", "data_origin": "synthetic",
        "status": "synthetic_fixture", "config": config,
        "questions": [{"question_uuid": "synthetic_question", "statement": "Synthetic question: 2 + 2?",
                       "total_points": 10, "rubric_json": [{"name": "Synthetic rubric", "weight": 1,
                                                            "max_score": 10}]}],
        "answers": [{"question_uuid": "synthetic_question", "student_id": "synthetic_case_1",
                     "answer_text": "Synthetic answer: four."},
                    {"question_uuid": "synthetic_question", "student_id": "synthetic_case_2",
                     "answer_text": "Synthetic answer: two plus two equals four."}],
        "results": [{"question_uuid": "synthetic_question", "student_id": "synthetic_case_1",
                     "c1_score": 4, "c2_score": 8, "arbiter_score": 8,
                     "final_score": 8, "consensus_method": "closest_pair_3"},
                    {"question_uuid": "synthetic_question", "student_id": "synthetic_case_2",
                     "c1_score": 6, "c2_score": 8, "arbiter_score": None,
                     "final_score": 7, "consensus_method": "mean_2"}],
        "rag_contexts": [{"question_uuid": "synthetic_question", "student_id": case,
                          "chunk_content": "SYNTHETIC RETRIEVAL: Two plus two equals four.",
                          "source_document": "synthetic_fixture.txt", "page_number": 1, "rank": 1}
                         for case in ("synthetic_case_1", "synthetic_case_2")] if rag else [],
    }


class EvaluationExperimentTests(unittest.TestCase):
    def run_exports(self, a, b=None, thresholds=(0.5, 1.0, 1.5, 2.0)):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for index, item in enumerate([a] if b is None else [a, b]):
                path = Path(tmp) / f"export_{index}.json"
                path.write_text(json.dumps(item), encoding="utf-8")
                paths.append(path)
            return evaluate_experiments(paths, thresholds=thresholds)

    def test_lower_threshold_cannot_invent_missing_arbiter_or_reference(self):
        report = self.run_exports(synthetic_export())
        policy = report["arbitration"]["threshold_simulation"][0]
        self.assertEqual(policy["would_trigger"], 2)
        self.assertEqual(policy["observed_arbiter_available"], 1)
        self.assertFalse(policy["complete_policy_outcomes"])
        self.assertIsNone(policy["mean_absolute_score_shift"])
        self.assertIsNone(policy["reference_mae"])
        self.assertIsNone(policy["mean_observed_arbiter_latency_ms"])
        self.assertIsNone(policy["total_observed_arbiter_cost_usd"])
        self.assertIsNone(report["arbitration"]["reference_comparison"])

    def test_strict_threshold_replays_only_available_scores(self):
        report = self.run_exports(synthetic_export(), thresholds=(2, 4))
        first, second = report["arbitration"]["threshold_simulation"]
        self.assertEqual(first["would_trigger"], 1)
        self.assertTrue(first["complete_policy_outcomes"])
        self.assertEqual(first["mean_absolute_score_shift"], 1)
        self.assertEqual(second["would_trigger"], 0)  # Difference equal to threshold does not trigger.
        self.assertEqual(second["mean_absolute_score_shift"], 0)

    def test_exact_material_and_complete_config_can_demonstrate_pipeline(self):
        a, b = synthetic_export(True), synthetic_export(False)
        b["results"][0].update(c1_score=6, c2_score=6, arbiter_score=None, final_score=6)
        report = self.run_exports(a, b)
        comparison = report["rag"]["comparisons"][0]
        self.assertEqual(report["data_origin"], "synthetic_demonstration")
        self.assertEqual(comparison["exact_material_pairs"], 2)
        self.assertEqual(comparison["eligible_controlled_pairs"], 2)
        self.assertEqual(comparison["controlled_mean_score_shift"], 1)
        self.assertIsNone(comparison["reference_effect"])
        self.assertIsNone(report["rag"]["causal_quality_effect"])
        self.assertIsNone(comparison["pairs"][0]["observed_latency_delta_ms"])

    def test_same_identifiers_do_not_pair_different_answers_or_rubrics(self):
        a, b = synthetic_export(True), synthetic_export(False)
        b["answers"][0]["answer_text"] = "A different synthetic answer"
        comparison = self.run_exports(a, b)["rag"]["comparisons"][0]
        self.assertEqual(comparison["exact_material_pairs"], 1)
        self.assertEqual(len(comparison["unmatched_cases"]), 2)
        b["questions"][0]["rubric_json"][0]["weight"] = 0.9
        comparison = self.run_exports(a, b)["rag"]["comparisons"][0]
        self.assertEqual(comparison["exact_material_pairs"], 0)
        self.assertIsNone(comparison["mean_score_shift_descriptive"])

    def test_missing_or_changed_configuration_blocks_controlled_effect(self):
        a, b = synthetic_export(True), synthetic_export(False)
        del a["config"]["llm_temperature"]
        b["config"]["llm_model"] = "another_synthetic_model"
        comparison = self.run_exports(a, b)["rag"]["comparisons"][0]
        self.assertEqual(comparison["exact_material_pairs"], 2)
        self.assertEqual(comparison["eligible_controlled_pairs"], 0)
        self.assertIsNone(comparison["controlled_mean_score_shift"])
        reasons = comparison["pairs"][0]["blocking_reasons"]
        self.assertIn("unknown_configuration:llm_temperature", reasons)
        self.assertIn("configuration_mismatch:llm_model", reasons)

    def test_missing_context_content_blocks_despite_rag_boolean(self):
        a, b = synthetic_export(True), synthetic_export(False)
        a["rag_contexts"] = [{"question_uuid": "synthetic_question", "student_id": "synthetic_case_1",
                              "source_document": "a_filename_is_not_retrieval_content"}]
        comparison = self.run_exports(a, b)["rag"]["comparisons"][0]
        self.assertEqual(comparison["eligible_controlled_pairs"], 0)
        for pair in comparison["pairs"]:
            self.assertIn("retrieval_evidence_missing", pair["blocking_reasons"])

    def test_arbiter_or_consensus_change_blocks_controlled_final_score_comparison(self):
        a, b = synthetic_export(True), synthetic_export(False)
        del a["config"]["source_fingerprints"]["arbiter_runtime_file_sha256"]
        b["config"]["source_fingerprints"]["consensus_runtime_file_sha256"] = "1" * 64
        comparison = self.run_exports(a, b)["rag"]["comparisons"][0]
        self.assertEqual(comparison["eligible_controlled_pairs"], 0)
        self.assertIn("unknown_configuration:arbiter_runtime_file_sha256",
                      comparison["configuration_blocking_reasons"])
        self.assertIn("configuration_mismatch:consensus_runtime_file_sha256",
                      comparison["configuration_blocking_reasons"])

    def test_malformed_hash_or_truncated_excerpt_cannot_stand_for_full_context(self):
        a, b = synthetic_export(True), synthetic_export(False)
        a["rag_contexts"][0]["chunk_sha256"] = "z" * 64
        a["rag_contexts"][1]["content_truncated"] = True
        comparison = self.run_exports(a, b)["rag"]["comparisons"][0]
        self.assertEqual(comparison["eligible_controlled_pairs"], 0)

    def test_ambiguous_identical_material_is_not_cartesian_joined(self):
        a, b = synthetic_export(True), synthetic_export(False)
        duplicate = copy.deepcopy(a["results"][0])
        duplicate["student_id"] = "duplicate_material_case"
        a["results"].append(duplicate)
        a["answers"].append({"question_uuid": "synthetic_question", "student_id": "duplicate_material_case",
                             "answer_text": a["answers"][0]["answer_text"]})
        comparison = self.run_exports(a, b)["rag"]["comparisons"][0]
        self.assertEqual(comparison["exact_material_pairs"], 1)
        self.assertEqual(len(comparison["unmatched_cases"]), 3)
        self.assertTrue(all(r["reason"] == "ambiguous_duplicate_material"
                            for r in comparison["unmatched_cases"]))

    def test_synthetic_and_history_cannot_be_pooled(self):
        a, b = synthetic_export(True), synthetic_export(False)
        b.pop("data_origin")
        b["config"].pop("data_origin")
        with self.assertRaisesRegex(ValueError, "evaluated separately"):
            self.run_exports(a, b)

    def test_duplicate_case_and_nan_threshold_are_rejected(self):
        a = synthetic_export(True)
        a["results"].append(copy.deepcopy(a["results"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.run_exports(a)
        with self.assertRaisesRegex(ValueError, "finite"):
            self.run_exports(synthetic_export(), thresholds=(float("nan"),))

    def test_only_explicit_nonnegative_observed_measurements_are_reported(self):
        a, b = synthetic_export(True), synthetic_export(False)
        b["results"][0].update(c1_score=6, c2_score=6, arbiter_score=None, final_score=6)
        a["results"][0]["processing_metadata"] = {
            "arbiter_elapsed_ms": 12, "arbiter_cost_usd": 0.003,
            "total_elapsed_ms": 30, "cost_usd": 0.006,
        }
        b["results"][0]["processing_metadata"] = {"total_elapsed_ms": 20, "cost_usd": 0.002}
        report = self.run_exports(a, b, thresholds=(2,))
        policy = report["arbitration"]["threshold_simulation"][0]
        self.assertEqual(policy["mean_observed_arbiter_latency_ms"], 12)
        self.assertEqual(policy["total_observed_arbiter_cost_usd"], 0.003)
        pair = next(p for p in report["rag"]["comparisons"][0]["pairs"]
                    if p["rag_final_score"] == 8)
        self.assertEqual(pair["observed_latency_delta_ms"], 10)
        self.assertEqual(pair["observed_cost_delta_usd"], 0.004)
        a["results"][0]["processing_metadata"]["arbiter_elapsed_ms"] = -1
        policy = self.run_exports(a, b, thresholds=(2,))["arbitration"]["threshold_simulation"][0]
        self.assertIsNone(policy["mean_observed_arbiter_latency_ms"])

    def test_failed_empty_export_stays_visible(self):
        a = synthetic_export(True)
        a["results"] = []
        a["status"] = "completed"
        a["config"]["final_status"] = "TIMEOUT"
        failure = self.run_exports(a)["source_failures"][0]
        self.assertEqual(failure["status"], "TIMEOUT")
        self.assertIn("no_recorded_outcomes", failure["flags"])
        self.assertIn("export_status_conflicts_with_execution_status", failure["flags"])

    def test_deterministic_report(self):
        a, b = synthetic_export(True), synthetic_export(False)
        self.assertEqual(self.run_exports(a, b), self.run_exports(a, b))


if __name__ == "__main__":
    unittest.main()
