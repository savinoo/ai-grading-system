"""Reference-label provenance gates; all declarations here are synthetic fixtures."""
import copy
import unittest

from evaluation.annotation import (import_annotations, load_gold, material_hash, reference_for,
                                   synthetic_demo, validate_gold)


class AnnotationTests(unittest.TestCase):
    def setUp(self):
        self.packet, self.demo = synthetic_demo()

    def declared_human_fixture(self):
        obj = copy.deepcopy(self.demo)
        # This tests an external provenance declaration, not a real human rating.
        obj["label_origin"] = "human"
        return obj

    def test_synthetic_demo_runs_import_without_becoming_human_reference(self):
        self.assertEqual(self.demo["import_validation"]["adjudicated_cases"], 1)
        with self.assertRaisesRegex(ValueError, "Only recorded human"):
            validate_gold(self.demo)
        labels = validate_gold(self.demo, allow_synthetic=True)
        case = self.packet["items"][0]
        question = {"statement": case["statement"], "rubric": case["rubric"], "total_points": case["total_points"]}
        self.assertIsNone(reference_for(labels, (case["question_uuid"], case["student_id"]), question, case["answer_text"]))

    def test_material_requires_explicit_valid_scale_and_rubric(self):
        item = self.packet["items"][0]
        self.assertIsNotNone(material_hash(item, item["answer_text"]))
        for points in (None, False, 0, -1, float("nan"), float("inf")):
            changed = {**item, "total_points": points}
            self.assertIsNone(material_hash(changed, item["answer_text"]))
        for rubric in ({"bad": "shape"}, ["bad"], [{"name": "x", "weight": 1}],
                       [{"name": "x", "weight": 0.8, "max_score": 10}]):
            changed = {**item, "rubric": rubric}
            self.assertIsNone(material_hash(changed, item["answer_text"]))

    def test_import_rechecks_packet_content_not_only_declared_hash(self):
        packet = copy.deepcopy(self.packet)
        packet["items"][0]["answer_text"] = "Changed after freezing"
        with self.assertRaisesRegex(ValueError, "fingerprint does not match its content"):
            import_annotations(packet, self.declared_human_fixture())

    def test_recorded_two_reviewers_and_adjudication_required(self):
        obj = self.declared_human_fixture()
        obj["items"][0]["independent_ratings"] = obj["items"][0]["independent_ratings"][:1]
        with self.assertRaisesRegex(ValueError, "two recorded"):
            validate_gold(obj)
        obj = self.declared_human_fixture()
        obj["items"][0]["independent_ratings"][1]["reviewer_id"] = "synthetic-rater-A"
        with self.assertRaisesRegex(ValueError, "distinct"):
            validate_gold(obj)
        obj = self.declared_human_fixture()
        obj["items"][0]["adjudication"] = None
        with self.assertRaisesRegex(ValueError, "Adjudicator"):
            validate_gold(obj)

    def test_model_unblinded_or_material_mismatch_rejected(self):
        obj = self.declared_human_fixture()
        obj["items"][0]["independent_ratings"][0]["blinded_to_model_scores"] = False
        with self.assertRaisesRegex(ValueError, "blindness"):
            validate_gold(obj)
        obj = self.declared_human_fixture()
        obj["items"][0]["independent_ratings"][0]["material_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
            validate_gold(obj)

    def test_import_checks_frozen_rubric_and_totals(self):
        obj = self.declared_human_fixture()
        result = import_annotations(self.packet, obj)
        self.assertEqual(result["import_validation"]["adjudicated_cases"], 1)
        obj["items"][0]["independent_ratings"][0]["criterion_scores"][0]["score"] = 8.0
        with self.assertRaisesRegex(ValueError, "weighted criterion"):
            import_annotations(self.packet, obj)
        obj = self.declared_human_fixture()
        obj["items"][0]["adjudication"]["criterion_scores"][0]["criterion"] = "invented-rubric"
        with self.assertRaisesRegex(ValueError, "exact frozen rubric"):
            import_annotations(self.packet, obj)

    def test_import_rejects_unknown_material_or_dataset(self):
        obj = self.declared_human_fixture()
        obj["provenance"]["dataset_id"] = "somewhere-else"
        with self.assertRaisesRegex(ValueError, "dataset"):
            import_annotations(self.packet, obj)
        obj = self.declared_human_fixture()
        obj["items"][0]["student_id"] = "unknown-case"
        with self.assertRaisesRegex(ValueError, "absent from frozen"):
            import_annotations(self.packet, obj)

    def test_legacy_or_missing_provenance_cannot_assert_gold(self):
        with self.assertRaisesRegex(ValueError, "schema_version=2"):
            validate_gold({"schema_version": 1, "items": []})
        obj = self.declared_human_fixture()
        obj["provenance"] = {}
        with self.assertRaisesRegex(ValueError, "dataset_id"):
            validate_gold(obj)

    def test_multiple_answer_versions_require_their_exact_reference(self):
        obj = self.declared_human_fixture()
        second = copy.deepcopy(obj["items"][0])
        second["material_sha256"] = "1" * 64
        for rating in second["independent_ratings"]:
            rating["material_sha256"] = second["material_sha256"]
        second["adjudication"]["material_sha256"] = second["material_sha256"]
        obj["items"].append(second)
        labels = validate_gold(obj)
        self.assertEqual(len(labels.by_material), 2)
        case = self.packet["items"][0]
        question = {"statement": case["statement"], "rubric": case["rubric"], "total_points": case["total_points"]}
        self.assertEqual(reference_for(labels, (case["question_uuid"], case["student_id"]), question, case["answer_text"]), 10.0)
        self.assertIsNone(reference_for(labels, (case["question_uuid"], case["student_id"]), question, "different"))


if __name__ == "__main__":
    unittest.main()
