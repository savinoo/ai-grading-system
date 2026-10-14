"""Regression tests for persistence of per-criterion examiner scores.

Run without external services:
    python -m unittest discover -s tests -p "test_experiment_store.py" -v
"""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.experiment_store import ExperimentStore


class ExperimentStoreCriteriaTests(unittest.TestCase):
    def test_criteria_scores_are_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ExperimentStore(str(Path(directory) / "experiments.db"))
            exp_id = store.create_experiment({"condition": "criterion persistence smoke test"})
            correction = SimpleNamespace(
                total_score=7.5,
                reasoning_chain="Test explanation for criterion persistence.",
                feedback_text="Feedback",
                confidence_level=0.8,
                criteria_scores=[
                    SimpleNamespace(criterion="Technical accuracy", score=7.5, max_score=10.0, feedback="ok"),
                ],
            )
            store.save_correction(exp_id, "question-1", "student-1", correction, "corretor_1")
            exported = store.export_experiment(exp_id)
            self.assertEqual(len(exported["corrections"]), 1)
            self.assertEqual(exported["corrections"][0]["criterion_scores"][0]["criterion"], "Technical accuracy")
            self.assertEqual(exported["corrections"][0]["criterion_scores"][0]["score"], 7.5)
            store.conn.close()

    def test_missing_correction_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ExperimentStore(str(Path(directory) / "experiments.db"))
            exp_id = store.create_experiment({"condition": "missing correction"})
            store.save_correction(exp_id, "question-1", "student-1", None, "corretor_1")
            self.assertEqual(store.export_experiment(exp_id)["corrections"], [])
            store.conn.close()


if __name__ == "__main__":
    unittest.main()
