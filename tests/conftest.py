"""
Shared pytest fixtures for the AI Grading System test suite.
All fixtures produce domain objects with realistic but deterministic data.
No external services or API keys required.
"""
import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Pre-import stubs for heavy/optional dependencies that are NOT installed in
# the test environment. These must be injected BEFORE any src module tries to
# import them at collection time.
# ---------------------------------------------------------------------------

def _ensure_stub(module_name: str) -> None:
    """Insert a MagicMock into sys.modules if the real module is absent."""
    if module_name not in sys.modules:
        sys.modules[module_name] = MagicMock()

# streamlit (used by src.utils.helpers at module level)
_ensure_stub("streamlit")

# python-dotenv (used by src.config.settings at module level)
_ensure_stub("dotenv")
# make load_dotenv a no-op callable
sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None

# langchain / chroma / embedding dependencies
for _mod in (
    "langchain_chroma",
    "langchain_google_genai",
    "langchain_openai",
    "langchain_core",
    "langchain_core.language_models",
    "langchain_core.prompts",
    "chromadb",
):
    _ensure_stub(_mod)

# openai (used by src.agents.examiner)
_ensure_stub("openai")

# langsmith (used by src.agents.examiner via @traceable)
_ensure_stub("langsmith")
# Make traceable a passthrough decorator
sys.modules["langsmith"].traceable = lambda *a, **kw: (lambda fn: fn)

# tenacity (used by src.agents.examiner for retry logic)
_ensure_stub("tenacity")
# Provide no-op decorators for retry, stop_after_attempt, etc.
sys.modules["tenacity"].retry = lambda **kw: (lambda fn: fn)
sys.modules["tenacity"].stop_after_attempt = lambda *a: None
sys.modules["tenacity"].wait_exponential = lambda **kw: None
sys.modules["tenacity"].retry_if_exception_type = lambda *a: None

# numpy is a real dependency (installed); no stub needed.
# It is required by src.analytics.student_tracker and also by pytest.approx.

# dspy (used by test_gemini_connection)
_ensure_stub("dspy")

# ---------------------------------------------------------------------------
# Normal imports (safe now that stubs are in place)
# ---------------------------------------------------------------------------
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


@pytest.fixture
def sample_criteria():
    """Two evaluation criteria that sum to 10 points."""
    return [
        EvaluationCriterion(
            name="Precisao Conceitual",
            description="O aluno demonstra conhecimento correto dos conceitos.",
            weight=6.0,
            max_score=10.0,
        ),
        EvaluationCriterion(
            name="Clareza e Organizacao",
            description="A resposta esta bem estruturada e clara.",
            weight=4.0,
            max_score=10.0,
        ),
    ]


@pytest.fixture
def sample_question(sample_criteria):
    """A fully populated ExamQuestion."""
    return ExamQuestion(
        id="Q001",
        statement="Explique a diferenca entre uma arvore binaria de busca e uma arvore AVL.",
        rubric=sample_criteria,
        metadata=QuestionMetadata(
            discipline="Estrutura de Dados",
            topic="Arvores Binarias",
            difficulty_level="medium",
        ),
    )


@pytest.fixture
def sample_answer():
    """A StudentAnswer linked to Q001."""
    return StudentAnswer(
        student_id="STU-001",
        question_id="Q001",
        text="Uma arvore AVL e uma arvore binaria de busca balanceada que garante O(log n).",
    )


@pytest.fixture
def sample_rag_context():
    """A list of two RetrievedContext chunks."""
    return [
        RetrievedContext(
            content="Uma arvore AVL realiza rotacoes para manter o fator de balanceamento entre -1 e 1.",
            source_document="slides_aula_05.pdf",
            page_number=12,
            relevance_score=0.92,
        ),
        RetrievedContext(
            content="Arvores binarias de busca nao garantem balanceamento, podendo degenerar em lista ligada.",
            source_document="livro_ed_cap7.pdf",
            page_number=45,
            relevance_score=0.85,
        ),
    ]


@pytest.fixture
def sample_criterion_scores():
    """A list of CriterionScore objects that sum to 8.0."""
    return [
        CriterionScore(criterion="Precisao Conceitual", score=5.0, feedback="Boa explicacao."),
        CriterionScore(criterion="Clareza e Organizacao", score=3.0, feedback="Poderia ser mais claro."),
    ]


@pytest.fixture
def sample_correction(sample_criterion_scores):
    """A valid AgentCorrection with pre-computed scores."""
    return AgentCorrection(
        agent_id=AgentID.CORRETOR_1,
        reasoning_chain="Passo 1: Verificar conceitos. Passo 2: Avaliar clareza.",
        criteria_scores=sample_criterion_scores,
        feedback_text="Resposta satisfatoria, mas precisa de mais detalhes.",
    )
