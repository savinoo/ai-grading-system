"""Frozen-source, deidentification and independent-cohort regression checks."""
import hashlib
import json
import unittest
from pathlib import Path

from evaluation.dataset import SOURCE_COMMIT, normalize_export, normalize_notebook

ROOT = Path(__file__).resolve().parents[1] / "evaluation" / "data"


class FrozenDatasetTests(unittest.TestCase):
    def test_frozen_manifest_hashes_match_reviewed_artifacts(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        self.assertEqual(manifest["source_commit"], SOURCE_COMMIT)
        self.assertEqual(manifest["normalized_exports"], 16)
        self.assertGreater(len(manifest["sources"]), 16)
        for row in manifest["outputs"]:
            with self.subTest(path=row["path"]):
                self.assertEqual(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(), row["sha256"])

    def test_two_qa4_cohorts_remain_separate_and_unlabelled(self):
        report = json.loads((ROOT / "reliability_report.json").read_text())
        notebook = json.loads((ROOT / "qa4_notebook_report.json").read_text())
        self.assertEqual((report["total_corrections"], report["unique_cases"]), (36, 12))
        self.assertEqual((notebook["total_corrections"], notebook["unique_cases"]), (12, 4))
        self.assertEqual(max(row["score_range"] for row in report["stability"]), 0.625)
        self.assertEqual(max(row["score_range"] for row in notebook["stability"]), 1.37)
        self.assertEqual([r["would_trigger"] for r in report["threshold_simulation"]], [8, 3, 1, 0])
        self.assertTrue(all(not row["verified_identical_answer"] for row in report["stability"]))
        self.assertTrue(all(row["verified_identical_material"] for row in notebook["stability"]))
        self.assertTrue(any("exported_divergence_inconsistent" in row["flags"] for row in notebook["records"]))
        self.assertIsNone(report["reference_metrics"])
        self.assertIsNone(notebook["reference_metrics"])

    def test_normalization_excludes_identity_and_keeps_unknowns_unknown(self):
        original = {"id": 1, "status": "FAILED", "config": {"rag_enabled": True, "secret": "never-copy", "final_status": "TIMEOUT"},
            "questions": [{"question_uuid": "raw-q", "statement": "Question?", "total_points": 10, "rubric_json": "[]"}],
            "students": [{"student_id": "raw-s", "student_name": "PRIVATE NAME", "email": "private@example.org", "quality_profile": "poor"}],
            "answers": [{"question_uuid": "raw-q", "student_id": "raw-s", "answer_text": "Synthetic answer", "student_name": "PRIVATE NAME"}],
            "rag_contexts": [{"question_uuid": "raw-q", "student_id": "raw-s", "chunk_content": "x" * 500,
                              "source_document": "/private/owner/textbook.pdf", "page_number": 4}],
            "corrections": [], "results": []}
        obj = normalize_export(original, {"source_path": "test.json", "source_family": "fixture"})
        serialized = json.dumps(obj)
        for forbidden in ("PRIVATE NAME", "private@example.org", "raw-q", "raw-s", "never-copy", "/private/owner/"):
            self.assertNotIn(forbidden, serialized)
        self.assertNotIn("llm_temperature", obj["config"])
        self.assertEqual(obj["status"], "FAILED")
        self.assertEqual(obj["config"]["final_status"], "TIMEOUT")
        context = obj["rag_contexts"][0]
        self.assertEqual(context["chunk_sha256"], hashlib.sha256(b"x" * 500).hexdigest())
        self.assertEqual(len(context["chunk_content"]), 240)
        self.assertTrue(context["content_truncated"])

    def test_annotation_packet_has_material_but_no_model_scores_or_profile(self):
        packet = json.loads((ROOT / "annotation" / "blind_packet.json").read_text())
        template = json.loads((ROOT / "annotation" / "ratings_template.json").read_text())
        self.assertEqual(len(packet["items"]), 48)
        for item in packet["items"]:
            self.assertTrue(item["answer_text"])
            self.assertTrue(item["rubric"])
            self.assertNotIn("profile", item)
            self.assertNotIn("final_score", item)
            self.assertNotIn("c1_score", item)
            self.assertNotIn("sources", item)
        self.assertTrue(all(row["reference_score"] is None for row in template["items"]))
        self.assertTrue(all(row["review_status"] == "unreviewed" for row in template["items"]))


if __name__ == "__main__":
    unittest.main()
