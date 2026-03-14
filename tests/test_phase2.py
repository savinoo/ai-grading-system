"""
Phase 2 Tests - SQLite storage, configurable thresholds, plagiarism detection, GDPR.
"""
import json
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from src.analytics import StudentTracker
from src.analytics.plagiarism_detector import PlagiarismDetector, PlagiarismReport
from src.domain.analytics_schemas import StudentProfile, SubmissionRecord
from src.memory.student_knowledge_base import StudentKnowledgeBase


class TestSQLiteKnowledgeBase:
    """Tests for the SQLite-backed StudentKnowledgeBase."""

    def _make_kb(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        return StudentKnowledgeBase(db_path=db_path)

    def _make_profile(self, student_id="S001", name="Test Student", grade=8.0):
        sub = SubmissionRecord(
            submission_id="SUB001",
            question_id="Q1",
            question_text="Test question",
            student_answer="Test answer",
            grade=grade,
            max_score=10.0,
            criterion_scores={"Precisão": 7.5, "Clareza": 8.5},
        )
        profile = StudentProfile(
            student_id=student_id,
            student_name=name,
            submissions_history=[sub],
            avg_grade=grade,
            submission_count=1,
            first_submission=datetime.now(),
            last_submission=datetime.now(),
            last_updated=datetime.now(),
        )
        return profile

    def test_create_and_retrieve(self, tmp_path):
        """Test basic add and get."""
        kb = self._make_kb(tmp_path)
        profile = self._make_profile()
        kb.add_or_update(profile)

        loaded = kb.get("S001")
        assert loaded is not None
        assert loaded.student_id == "S001"
        assert loaded.student_name == "Test Student"
        assert loaded.avg_grade == 8.0
        assert len(loaded.submissions_history) == 1
        assert loaded.submissions_history[0].grade == 8.0

    def test_get_all(self, tmp_path):
        """Test retrieving all profiles."""
        kb = self._make_kb(tmp_path)
        kb.add_or_update(self._make_profile("S001", "Alice", 9.0))
        kb.add_or_update(self._make_profile("S002", "Bob", 7.0))

        all_profiles = kb.get_all()
        assert len(all_profiles) == 2

    def test_delete_cascade(self, tmp_path):
        """Test that deleting a student cascades to submissions, gaps, strengths."""
        kb = self._make_kb(tmp_path)
        kb.add_or_update(self._make_profile())
        assert kb.get("S001") is not None

        kb.delete("S001")
        assert kb.get("S001") is None

        # Verify cascade
        row = kb.conn.execute("SELECT COUNT(*) FROM submissions WHERE student_id = 'S001'").fetchone()
        assert row[0] == 0

    def test_update_existing_profile(self, tmp_path):
        """Test that updating an existing profile replaces data."""
        kb = self._make_kb(tmp_path)
        kb.add_or_update(self._make_profile("S001", "Alice", 7.0))
        kb.add_or_update(self._make_profile("S001", "Alice Updated", 9.5))

        loaded = kb.get("S001")
        assert loaded.student_name == "Alice Updated"
        assert loaded.avg_grade == 9.5

    def test_persistence_across_instances(self, tmp_path):
        """Test data survives closing and reopening the database."""
        db_path = str(tmp_path / "persist.db")

        kb1 = StudentKnowledgeBase(db_path=db_path)
        kb1.add_or_update(self._make_profile("S001", "Alice", 8.0))
        kb1.close()

        kb2 = StudentKnowledgeBase(db_path=db_path)
        loaded = kb2.get("S001")
        assert loaded is not None
        assert loaded.student_name == "Alice"
        kb2.close()

    def test_clear_old_submissions(self, tmp_path):
        """Test that old submissions are cleaned up."""
        kb = self._make_kb(tmp_path)

        old_sub = SubmissionRecord(
            submission_id="OLD001",
            question_id="Q1",
            question_text="Old question",
            student_answer="Old answer",
            grade=5.0,
            max_score=10.0,
            timestamp=datetime.now() - timedelta(days=400),
        )
        new_sub = SubmissionRecord(
            submission_id="NEW001",
            question_id="Q2",
            question_text="New question",
            student_answer="New answer",
            grade=9.0,
            max_score=10.0,
            timestamp=datetime.now(),
        )

        profile = StudentProfile(
            student_id="S001",
            student_name="Test",
            submissions_history=[old_sub, new_sub],
            avg_grade=7.0,
            submission_count=2,
            last_updated=datetime.now(),
        )
        kb.add_or_update(profile)

        removed = kb.clear_old_submissions(days_to_keep=365)
        assert removed == 1

        # Only new submission remains
        row = kb.conn.execute("SELECT COUNT(*) FROM submissions WHERE student_id = 'S001'").fetchone()
        assert row[0] == 1

    def test_export_student_history(self, tmp_path):
        """Test JSON export."""
        kb = self._make_kb(tmp_path)
        kb.add_or_update(self._make_profile())

        output = str(tmp_path / "export.json")
        kb.export_student_history("S001", output)

        assert os.path.exists(output)
        with open(output) as f:
            data = json.load(f)
        assert data["student_id"] == "S001"

    def test_export_and_anonymize(self, tmp_path):
        """Test GDPR anonymization export."""
        kb = self._make_kb(tmp_path)
        kb.add_or_update(self._make_profile())

        output = str(tmp_path / "anon.json")
        kb.export_and_anonymize("S001", output)

        # Original should be deleted
        assert kb.get("S001") is None

        # Anonymized file should exist
        assert os.path.exists(output)
        with open(output) as f:
            data = json.load(f)
        assert data["student_id"].startswith("ANON-")
        assert data["student_name"].startswith("Anonimizado-")
        # Answers should be anonymized
        for sub in data["submissions_history"]:
            assert sub["student_answer"] == "[ANONYMIZED]"

    def test_json_migration(self, tmp_path):
        """Test auto-migration from old JSON format."""
        # Create old-format JSON
        json_path = tmp_path / "student_profiles.json"
        old_data = {
            "S001": {
                "student_id": "S001",
                "student_name": "Legacy Student",
                "submissions_history": [
                    {
                        "submission_id": "SUB001",
                        "question_id": "Q1",
                        "question_text": "Test",
                        "student_answer": "Answer",
                        "grade": 7.5,
                        "max_score": 10.0,
                        "timestamp": datetime.now().isoformat(),
                        "criterion_scores": {},
                        "divergence_detected": False,
                        "feedback": None,
                    }
                ],
                "learning_gaps": [],
                "strengths": [],
                "avg_grade": 7.5,
                "submission_count": 1,
                "trend": "insufficient_data",
                "trend_confidence": 0.0,
                "first_submission": datetime.now().isoformat(),
                "last_submission": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }
        }
        with open(json_path, "w") as f:
            json.dump(old_data, f, default=str)

        # Create KB pointing to same directory -> should auto-migrate
        db_path = str(tmp_path / "student_profiles.db")
        kb = StudentKnowledgeBase(db_path=db_path)

        loaded = kb.get("S001")
        assert loaded is not None
        assert loaded.student_name == "Legacy Student"

        # JSON should be renamed to .bak
        assert not json_path.exists()
        assert (tmp_path / "student_profiles.json.bak").exists()
        kb.close()


class TestConfigurableThresholds:
    """Tests for configurable gap/strength thresholds."""

    def test_custom_gap_threshold(self):
        """Test that custom gap threshold is respected."""
        tracker = StudentTracker(gap_threshold=7.0, strength_threshold=9.0)

        for i in range(5):
            sub = SubmissionRecord(
                submission_id=f"SUB{i}",
                question_id=f"Q{i}",
                question_text=f"Q {i}",
                student_answer="A",
                grade=6.5,
                max_score=10.0,
                criterion_scores={"Precisão": 6.5},
            )
            tracker.add_submission("S001", "Test", sub)

        profile = tracker.get_profile("S001")
        # With threshold 7.0, avg 6.5 should be a gap
        gap_names = [g.criterion_name for g in profile.learning_gaps]
        assert "Precisão" in gap_names

    def test_default_threshold_no_gap(self):
        """Test that score above default threshold (6.0) is not flagged."""
        tracker = StudentTracker(gap_threshold=6.0)

        for i in range(5):
            sub = SubmissionRecord(
                submission_id=f"SUB{i}",
                question_id=f"Q{i}",
                question_text=f"Q {i}",
                student_answer="A",
                grade=7.0,
                max_score=10.0,
                criterion_scores={"Precisão": 6.5},
            )
            tracker.add_submission("S001", "Test", sub)

        profile = tracker.get_profile("S001")
        gap_names = [g.criterion_name for g in profile.learning_gaps]
        assert "Precisão" not in gap_names

    def test_custom_strength_threshold(self):
        """Test that custom strength threshold is respected."""
        tracker = StudentTracker(gap_threshold=6.0, strength_threshold=7.0)

        for i in range(5):
            sub = SubmissionRecord(
                submission_id=f"SUB{i}",
                question_id=f"Q{i}",
                question_text=f"Q {i}",
                student_answer="A",
                grade=8.0,
                max_score=10.0,
                criterion_scores={"Clareza": 7.5},
            )
            tracker.add_submission("S001", "Test", sub)

        profile = tracker.get_profile("S001")
        strength_names = [s.criterion_name for s in profile.strengths]
        # With threshold 7.0, avg 7.5 should be a strength
        assert "Clareza" in strength_names


class TestPlagiarismDetector:
    """Tests for the semantic plagiarism detector."""

    def test_identical_answers_flagged(self):
        """Test that identical long answers are flagged."""
        answer = (
            "Uma árvore AVL é uma árvore binária de busca auto-balanceada onde a diferença "
            "entre as alturas das subárvores esquerda e direita de qualquer nó é no máximo um. "
            "Quando essa propriedade é violada após uma inserção ou remoção, rotações são "
            "realizadas para restaurar o balanceamento. Existem quatro tipos de rotações: "
            "simples à esquerda, simples à direita, dupla à esquerda e dupla à direita."
        )

        submissions = [
            {"student_id": "S001", "student_name": "Alice", "question_id": "Q1", "answer": answer},
            {"student_id": "S002", "student_name": "Bob", "question_id": "Q1", "answer": answer},
        ]

        detector = PlagiarismDetector(threshold=0.90)
        report = detector.check_batch(submissions)

        assert report.has_flags
        assert len(report.flagged_pairs) == 1
        assert report.flagged_pairs[0].similarity_score >= 0.90

    def test_different_answers_not_flagged(self):
        """Test that genuinely different answers are not flagged."""
        submissions = [
            {
                "student_id": "S001",
                "student_name": "Alice",
                "question_id": "Q1",
                "answer": (
                    "Uma árvore AVL é uma estrutura de dados auto-balanceada que mantém "
                    "a altura em O(log n). Ela usa rotações simples e duplas para manter "
                    "o fator de balanceamento entre menos um e mais um após cada operação."
                ),
            },
            {
                "student_id": "S002",
                "student_name": "Bob",
                "question_id": "Q1",
                "answer": (
                    "Listas ligadas são estruturas de dados lineares onde cada elemento "
                    "contém um ponteiro para o próximo. Diferente de arrays, não precisam "
                    "de memória contígua e permitem inserção eficiente no início da lista."
                ),
            },
        ]

        detector = PlagiarismDetector(threshold=0.90)
        report = detector.check_batch(submissions)

        assert not report.has_flags

    def test_short_answers_skipped(self):
        """Test that very short answers (< 20 words) are ignored."""
        submissions = [
            {"student_id": "S001", "student_name": "Alice", "question_id": "Q1", "answer": "Sim, AVL é balanceada."},
            {"student_id": "S002", "student_name": "Bob", "question_id": "Q1", "answer": "Sim, AVL é balanceada."},
        ]

        detector = PlagiarismDetector(threshold=0.90)
        report = detector.check_batch(submissions)

        assert report.total_comparisons == 0

    def test_different_questions_compared_separately(self):
        """Test that comparisons happen only within same question."""
        answer = (
            "Uma árvore AVL é uma árvore binária de busca auto-balanceada onde a diferença "
            "entre as alturas das subárvores esquerda e direita de qualquer nó é no máximo um. "
            "Quando essa propriedade é violada rotações são realizadas para restaurar."
        )

        submissions = [
            {"student_id": "S001", "student_name": "Alice", "question_id": "Q1", "answer": answer},
            {"student_id": "S002", "student_name": "Bob", "question_id": "Q2", "answer": answer},
        ]

        detector = PlagiarismDetector(threshold=0.90)
        report = detector.check_batch(submissions)

        # Different questions, should not be compared
        assert report.total_comparisons == 0

    def test_configurable_threshold(self):
        """Test that a lower threshold flags more pairs."""
        base_answer = (
            "Uma árvore AVL é uma árvore binária de busca auto-balanceada onde a diferença "
            "entre as alturas das subárvores esquerda e direita de qualquer nó é no máximo um."
        )

        submissions = [
            {"student_id": "S001", "student_name": "Alice", "question_id": "Q1", "answer": base_answer},
            {
                "student_id": "S002",
                "student_name": "Bob",
                "question_id": "Q1",
                "answer": base_answer + " As rotações podem ser simples ou duplas.",
            },
        ]

        strict = PlagiarismDetector(threshold=0.99)
        lenient = PlagiarismDetector(threshold=0.50)

        report_strict = strict.check_batch(submissions)
        report_lenient = lenient.check_batch(submissions)

        # Lenient should flag at least as many as strict
        assert len(report_lenient.flagged_pairs) >= len(report_strict.flagged_pairs)

    def test_empty_batch(self):
        """Test that empty submissions return clean report."""
        detector = PlagiarismDetector()
        report = detector.check_batch([])

        assert not report.has_flags
        assert report.total_comparisons == 0

    def test_report_sorted_by_score(self):
        """Test that flagged pairs are sorted highest similarity first."""
        answer = (
            "Uma árvore AVL é uma árvore binária de busca auto-balanceada onde a diferença "
            "entre as alturas das subárvores esquerda e direita de qualquer nó é no máximo um. "
            "Quando essa propriedade é violada após uma inserção ou remoção, rotações são "
            "realizadas para restaurar o balanceamento."
        )

        submissions = [
            {"student_id": "S001", "student_name": "Alice", "question_id": "Q1", "answer": answer},
            {"student_id": "S002", "student_name": "Bob", "question_id": "Q1", "answer": answer},
            {
                "student_id": "S003",
                "student_name": "Charlie",
                "question_id": "Q1",
                "answer": answer + " Extra texto diferenciado aqui para reduzir a similaridade um pouco.",
            },
        ]

        detector = PlagiarismDetector(threshold=0.70)
        report = detector.check_batch(submissions)

        if len(report.flagged_pairs) >= 2:
            for i in range(len(report.flagged_pairs) - 1):
                assert report.flagged_pairs[i].similarity_score >= report.flagged_pairs[i + 1].similarity_score
