"""End-to-end offline reanalysis and frozen-data integrity checks."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from evaluation.run import reproduce, verify_dataset

DATA = Path(__file__).resolve().parents[1] / "evaluation" / "data"


class LabReproductionTests(unittest.TestCase):
    def test_bundled_corpus_reproduces_separate_historical_cohorts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            receipt = reproduce(DATA, output)
            self.assertEqual(receipt["human_reference_labels_loaded"], 0)
            for name, bundled, rows, cases in (
                ("qa4_json", "reliability_report.json", 36, 12),
                ("qa4_notebook", "qa4_notebook_report.json", 12, 4),
            ):
                report = json.loads((output / name / "report.json").read_text())
                expected = json.loads((DATA / bundled).read_text())
                self.assertEqual(report["total_corrections"], rows)
                self.assertEqual(report["unique_cases"], cases)
                self.assertEqual(report["stability"], expected["stability"])
                self.assertEqual(report["agreement"], expected["agreement"])
                self.assertIsNone(report["reference_metrics"])
            experiments = json.loads((output / "experiments.json").read_text())
            self.assertEqual(experiments["data_origin"], "historical_exports")
            self.assertIsNone(experiments["rag"]["causal_quality_effect"])

    def test_changed_frozen_export_blocks_reanalysis(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "data"
            shutil.copytree(DATA, copied)
            path = next((copied / "exports").glob("*.json"))
            path.write_text(path.read_text() + " ")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                reproduce(copied, Path(directory) / "output")

    def test_unlisted_export_cannot_enter_verified_reanalysis(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "data"
            shutil.copytree(DATA, copied)
            original = next((copied / "exports").glob("*.json"))
            shutil.copyfile(original, copied / "exports" / "unmanifested.json")
            with self.assertRaisesRegex(ValueError, "unlisted or missing export"):
                reproduce(copied, Path(directory) / "output")

    def test_duplicate_manifest_entry_cannot_double_count_an_export(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "data"
            shutil.copytree(DATA, copied)
            path = copied / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["outputs"].append(next(entry for entry in manifest["outputs"] if entry["path"].startswith("exports/")))
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "duplicate output paths"):
                reproduce(copied, Path(directory) / "output")

    def test_manifest_cannot_read_outside_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps({
                "outputs": [{"path": "../private.txt", "sha256": "invalid"}]
            }))
            with self.assertRaisesRegex(ValueError, "inside the dataset"):
                verify_dataset(root)


if __name__ == "__main__":
    unittest.main()
