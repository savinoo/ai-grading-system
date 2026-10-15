"""Tests for non-secret provenance snapshots and stored retrieval metadata."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.experiment_provenance import build_experiment_config, source_fingerprints
from app.experiment_store import ExperimentStore


class ProvenanceTests(unittest.TestCase):
    def test_runtime_snapshot_has_no_secrets(self):
        settings = SimpleNamespace(
            LLM_PROVIDER="gemini", LLM_MODEL_NAME="gemini-2.5-flash",
            LLM_TEMPERATURE=0, EMBEDDING_PROVIDER="google",
            EMBEDDING_MODEL="embedding-test", RAG_TOP_K=4, DIVERGENCE_THRESHOLD=2,
            GOOGLE_API_KEY="THIS_MUST_NOT_BE_CAPTURED", SECRET_KEY="THIS_IS_A_SECRET",
        )
        snapshot = build_experiment_config(settings)
        self.assertEqual(snapshot["llm_model"], "gemini-2.5-flash")
        self.assertEqual(snapshot["rag_top_k"], 4)
        self.assertNotIn("GOOGLE_API_KEY", json.dumps(snapshot))
        self.assertNotIn("THIS_IS_A_SECRET", json.dumps(snapshot))
        self.assertEqual(len(snapshot["source_fingerprints"]["examiner_prompt_file_sha256"]), 64)
        self.assertEqual(len(snapshot["source_fingerprints"]["arbiter_runtime_file_sha256"]), 64)
        self.assertEqual(len(snapshot["source_fingerprints"]["consensus_runtime_file_sha256"]), 64)

    def test_missing_sources_explicitly_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            fingerprints = source_fingerprints(Path(tmp))
            self.assertTrue(all(value is None for value in fingerprints.values()))

    def test_processing_metadata_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ExperimentStore(str(Path(tmp) / "experiments.db"))
            experiment_id = store.create_experiment({"condition": "smoke"})
            c1 = SimpleNamespace(total_score=3.0)
            c2 = SimpleNamespace(total_score=5.0)
            store.save_result(experiment_id, "q1", "s1", {
                "correction_1": c1,
                "correction_2": c2,
                "divergence_value": 2.0,
                "divergence_detected": False,
                "final_score": 4.0,
                "processing_metadata": {
                    "retrieval_status": "completed",
                    "retrieval_context_count": 3,
                    "retrieval_elapsed_ms": 11.5,
                },
            })
            result = store.export_experiment(experiment_id)["results"][0]
            self.assertEqual(result["processing_metadata"]["retrieval_context_count"], 3)
            self.assertEqual(result["processing_metadata"]["retrieval_elapsed_ms"], 11.5)
            store.conn.close()

    def test_existing_sqlite_results_table_is_migrated(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "old.db"
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    CREATE TABLE experiment_results (
                        id INTEGER PRIMARY KEY, experiment_id INTEGER, question_uuid TEXT,
                        student_id TEXT, c1_score REAL, c2_score REAL, arbiter_score REAL,
                        divergence_detected INTEGER, divergence_value REAL,
                        final_score REAL, consensus_method TEXT
                    )
                """)
            store = ExperimentStore(str(db_path))
            columns = {row["name"] for row in store.conn.execute("PRAGMA table_info(experiment_results)")}
            self.assertIn("processing_metadata_json", columns)
            store.conn.close()


if __name__ == "__main__":
    unittest.main()
