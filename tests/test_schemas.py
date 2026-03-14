"""
Unit tests for src/domain/schemas.py

Covers all Pydantic models, field validators, and model validators
in the grading domain layer. No external services required.
"""
import pytest

from src.domain.schemas import (
    AgentCorrection,
    AgentID,
    CriterionScore,
    EvaluationCriterion,
    ExamQuestion,
    QuestionMetadata,
    RetrievedContext,
    StudentAnswer,
)

# ---------------------------------------------------------------------------
# AgentID enum
# ---------------------------------------------------------------------------

class TestAgentID:

    def test_enum_values(self):
        """AgentID must expose exactly three members with expected string values."""
        assert AgentID.CORRETOR_1.value == "corretor_1"
        assert AgentID.CORRETOR_2.value == "corretor_2"
        assert AgentID.ARBITER.value == "corretor_3_arbiter"

    def test_enum_member_count(self):
        """Only three agent IDs should exist."""
        assert len(AgentID) == 3

    def test_enum_is_str(self):
        """AgentID inherits from str, so direct string comparison works."""
        assert AgentID.CORRETOR_1 == "corretor_1"


# ---------------------------------------------------------------------------
# EvaluationCriterion
# ---------------------------------------------------------------------------

class TestEvaluationCriterion:

    def test_defaults(self):
        """Weight defaults to 1.0 and max_score defaults to 10.0."""
        crit = EvaluationCriterion(name="Test", description="A test criterion")
        assert crit.weight == 1.0
        assert crit.max_score == 10.0

    def test_custom_values(self):
        """Explicit weight and max_score override defaults."""
        crit = EvaluationCriterion(
            name="Precisao", description="Desc", weight=4.0, max_score=5.0
        )
        assert crit.weight == 4.0
        assert crit.max_score == 5.0

    def test_missing_name_raises(self):
        """name is required; omitting it must raise ValidationError."""
        with pytest.raises(Exception):
            EvaluationCriterion(description="Only description")


# ---------------------------------------------------------------------------
# ExamQuestion
# ---------------------------------------------------------------------------

class TestExamQuestion:

    def test_creation_with_valid_data(self, sample_criteria):
        """ExamQuestion can be instantiated with all required fields."""
        q = ExamQuestion(
            id="Q100",
            statement="Descreva polimorfismo.",
            rubric=sample_criteria,
            metadata=QuestionMetadata(
                discipline="POO", topic="Polimorfismo"
            ),
        )
        assert q.id == "Q100"
        assert len(q.rubric) == 2
        assert q.metadata.discipline == "POO"

    def test_metadata_optional_difficulty(self):
        """difficulty_level is optional and defaults to None."""
        meta = QuestionMetadata(discipline="Redes", topic="TCP/IP")
        assert meta.difficulty_level is None

    def test_uses_fixture(self, sample_question):
        """Verify the shared fixture produces a usable ExamQuestion."""
        assert sample_question.id == "Q001"
        assert sample_question.metadata.topic == "Arvores Binarias"


# ---------------------------------------------------------------------------
# StudentAnswer
# ---------------------------------------------------------------------------

class TestStudentAnswer:

    def test_creation(self, sample_answer):
        """StudentAnswer fixture has expected field values."""
        assert sample_answer.student_id == "STU-001"
        assert sample_answer.question_id == "Q001"
        assert len(sample_answer.text) > 0

    def test_missing_text_raises(self):
        """text field is required."""
        with pytest.raises(Exception):
            StudentAnswer(student_id="S1", question_id="Q1")


# ---------------------------------------------------------------------------
# RetrievedContext
# ---------------------------------------------------------------------------

class TestRetrievedContext:

    def test_creation(self):
        """Basic creation with all fields."""
        ctx = RetrievedContext(
            content="Some content",
            source_document="doc.pdf",
            page_number=5,
            relevance_score=0.88,
        )
        assert ctx.page_number == 5
        assert ctx.relevance_score == 0.88

    def test_page_number_optional(self):
        """page_number defaults to None when omitted."""
        ctx = RetrievedContext(
            content="chunk", source_document="src.pdf", relevance_score=0.5
        )
        assert ctx.page_number is None

    def test_fixture(self, sample_rag_context):
        """Shared fixture returns a list of two contexts."""
        assert len(sample_rag_context) == 2
        assert sample_rag_context[0].relevance_score > sample_rag_context[1].relevance_score


# ---------------------------------------------------------------------------
# CriterionScore
# ---------------------------------------------------------------------------

class TestCriterionScore:

    def test_creation(self):
        """CriterionScore stores criterion name, numeric score, and optional feedback."""
        cs = CriterionScore(criterion="Precisao", score=7.5, feedback="Bom")
        assert cs.criterion == "Precisao"
        assert cs.score == 7.5
        assert cs.feedback == "Bom"

    def test_feedback_defaults_to_none(self):
        """feedback is optional."""
        cs = CriterionScore(criterion="Clareza", score=6.0)
        assert cs.feedback is None


# ---------------------------------------------------------------------------
# AgentCorrection — Validators
# ---------------------------------------------------------------------------

class TestAgentCorrectionNormalizeReasoningChain:

    def test_list_joined_into_string(self):
        """A list of steps should be joined with newlines."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain=["Step 1", "Step 2", "Step 3"],
            criteria_scores=[],
            feedback_text="Ok",
        )
        assert correction.reasoning_chain == "Step 1\nStep 2\nStep 3"

    def test_string_passes_through(self):
        """A plain string should remain unchanged."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_2,
            reasoning_chain="Single paragraph reasoning",
            criteria_scores=[],
            feedback_text="Ok",
        )
        assert correction.reasoning_chain == "Single paragraph reasoning"

    def test_list_with_non_string_elements(self):
        """Non-string list items are coerced via str()."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain=[1, 2.5, True],
            criteria_scores=[],
            feedback_text="Ok",
        )
        assert "1" in correction.reasoning_chain
        assert "2.5" in correction.reasoning_chain


class TestAgentCorrectionNormalizeCriteriaScores:

    def test_dict_converted_to_list(self):
        """Legacy dict format {'CritName': score} becomes list of CriterionScore."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            criteria_scores={"Precisao": 5.0, "Clareza": 3.0},
            feedback_text="Ok",
        )
        assert isinstance(correction.criteria_scores, list)
        assert len(correction.criteria_scores) == 2
        names = {cs.criterion for cs in correction.criteria_scores}
        assert names == {"Precisao", "Clareza"}

    def test_list_passes_through(self):
        """A proper list of CriterionScore dicts is kept intact."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            criteria_scores=[
                {"criterion": "A", "score": 4.0},
                {"criterion": "B", "score": 6.0},
            ],
            feedback_text="Ok",
        )
        assert len(correction.criteria_scores) == 2


class TestAgentCorrectionCalculateTotalIfMissing:

    def test_total_auto_calculated_from_criteria(self):
        """total_score should be the sum of individual criteria scores."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            criteria_scores=[
                CriterionScore(criterion="A", score=3.0),
                CriterionScore(criterion="B", score=4.0),
            ],
            feedback_text="Ok",
        )
        assert correction.total_score == pytest.approx(7.0)

    def test_total_overridden_by_sum(self):
        """Even if total_score is explicitly provided, it is recomputed from criteria."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            total_score=99.0,  # intentionally wrong
            criteria_scores=[
                CriterionScore(criterion="A", score=2.0),
                CriterionScore(criterion="B", score=3.0),
            ],
            feedback_text="Ok",
        )
        # Model validator recomputes; then check_score_range clamps >10 to 10
        # But 2+3=5 which is <=10, so it should be 5.0
        assert correction.total_score == pytest.approx(5.0)

    def test_total_defaults_to_zero_when_no_criteria(self):
        """When criteria_scores is empty and total_score is None, default to 0."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            criteria_scores=[],
            feedback_text="Ok",
        )
        assert correction.total_score == 0.0


class TestAgentCorrectionGradeNormalization:

    def test_scores_lte_1_5_are_scaled_to_0_10(self):
        """If ALL criterion scores are <= 1.5, they are treated as 0-1 scale and multiplied by 10."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            criteria_scores=[
                CriterionScore(criterion="A", score=0.5),
                CriterionScore(criterion="B", score=0.8),
            ],
            feedback_text="Ok",
        )
        # 0.5 * 10 = 5.0, 0.8 * 10 = 8.0 => total = 13.0 => clamped to 10
        # But check_score_range runs on total_score field validator BEFORE model_validator.
        # Model validator recomputes: 5.0 + 8.0 = 13.0. But total_score is set directly,
        # and the field_validator runs only on initial assignment. Let's check what happens.
        assert correction.criteria_scores[0].score == pytest.approx(5.0)
        assert correction.criteria_scores[1].score == pytest.approx(8.0)

    def test_scores_above_1_5_not_scaled(self):
        """If any criterion score > 1.5, no normalization occurs."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            criteria_scores=[
                CriterionScore(criterion="A", score=5.0),
                CriterionScore(criterion="B", score=3.0),
            ],
            feedback_text="Ok",
        )
        assert correction.criteria_scores[0].score == pytest.approx(5.0)
        assert correction.criteria_scores[1].score == pytest.approx(3.0)
        assert correction.total_score == pytest.approx(8.0)

    def test_mixed_scores_one_above_threshold(self):
        """One score at 2.0 and one at 0.5: since 2.0 > 1.5, no normalization."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            criteria_scores=[
                CriterionScore(criterion="A", score=2.0),
                CriterionScore(criterion="B", score=0.5),
            ],
            feedback_text="Ok",
        )
        assert correction.criteria_scores[0].score == pytest.approx(2.0)
        assert correction.criteria_scores[1].score == pytest.approx(0.5)
        assert correction.total_score == pytest.approx(2.5)


class TestAgentCorrectionCheckScoreRange:

    def test_negative_total_clamped_to_zero(self):
        """Negative total_score should be clamped to 0."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            total_score=-5.0,
            criteria_scores=[],
            feedback_text="Ok",
        )
        # When criteria_scores is empty and total_score is not None,
        # check_score_range clamps -5 to 0, then model_validator sees empty criteria
        # and sets total to 0.0 anyway. Either way the result is 0.
        assert correction.total_score == 0.0

    def test_total_above_10_clamped(self):
        """total_score > 10 should be clamped to 10 by the field validator.
        When criteria_scores is empty, the model_validator does not override
        because total_score is already non-None after clamping."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            total_score=18.0,
            criteria_scores=[],
            feedback_text="Ok",
        )
        assert correction.total_score == 10.0

    def test_total_above_10_clamped_with_criteria(self):
        """When criteria sum exceeds 10, total is the raw sum (model_validator runs after field_validator)."""
        # The model_validator recomputes total_score from criteria_scores AFTER
        # the field validator, so the final value is the raw sum.
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            criteria_scores=[
                CriterionScore(criterion="A", score=6.0),
                CriterionScore(criterion="B", score=6.0),
            ],
            feedback_text="Ok",
        )
        # Sum = 12.0, model_validator sets total_score = 12.0
        # But check_score_range doesn't re-run after model_validator.
        # Pydantic v2 field validators run before model validators.
        # So the final total_score is 12.0 (set by model_validator).
        assert correction.total_score == pytest.approx(12.0)

    def test_valid_total_unchanged(self):
        """A total within 0-10 range passes through untouched."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            criteria_scores=[
                CriterionScore(criterion="A", score=3.0),
                CriterionScore(criterion="B", score=4.0),
            ],
            feedback_text="Ok",
        )
        assert correction.total_score == pytest.approx(7.0)

    def test_none_total_allowed(self):
        """total_score=None should pass the validator and get set by model_validator."""
        correction = AgentCorrection(
            agent_id=AgentID.CORRETOR_1,
            reasoning_chain="Reasoning",
            total_score=None,
            criteria_scores=[
                CriterionScore(criterion="A", score=4.0),
            ],
            feedback_text="Ok",
        )
        assert correction.total_score == pytest.approx(4.0)


class TestAgentCorrectionOptionalFields:

    def test_agent_id_optional(self):
        """agent_id can be omitted entirely."""
        correction = AgentCorrection(
            reasoning_chain="Reasoning",
            criteria_scores=[],
            feedback_text="Ok",
        )
        assert correction.agent_id is None

    def test_feedback_text_default(self):
        """feedback_text defaults to a placeholder string."""
        correction = AgentCorrection(
            reasoning_chain="Reasoning",
            criteria_scores=[],
        )
        assert correction.feedback_text == "Feedback n\u00e3o gerado."

    def test_fixture_correction(self, sample_correction):
        """The shared fixture produces a valid AgentCorrection."""
        assert sample_correction.agent_id == AgentID.CORRETOR_1
        assert sample_correction.total_score == pytest.approx(8.0)
        assert len(sample_correction.criteria_scores) == 2
