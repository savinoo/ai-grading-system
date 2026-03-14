"""
Unit tests for src/config/prompts.py

Covers the format_rubric_text and format_rag_context helper functions
used to interpolate structured data into LLM prompt templates.
No external services required.
"""

from src.config.prompts import format_rag_context, format_rubric_text
from src.domain.schemas import EvaluationCriterion, RetrievedContext

# ---------------------------------------------------------------------------
# format_rubric_text
# ---------------------------------------------------------------------------

class TestFormatRubricText:

    def test_single_criterion(self):
        """A single criterion produces one bullet with name, weight, and description."""
        criteria = [
            EvaluationCriterion(
                name="Precisao",
                description="Conceitos corretos",
                weight=6.0,
            )
        ]
        result = format_rubric_text(criteria)
        assert "Precisao" in result
        assert "6.0" in result
        assert "Conceitos corretos" in result

    def test_multiple_criteria(self, sample_criteria):
        """Each criterion in the list appears in the output."""
        result = format_rubric_text(sample_criteria)
        assert "Precisao Conceitual" in result
        assert "Clareza e Organizacao" in result
        # Both weights should appear
        assert "6.0" in result
        assert "4.0" in result

    def test_empty_list_returns_empty_string(self):
        """An empty rubric list produces an empty string."""
        result = format_rubric_text([])
        assert result == ""

    def test_output_contains_dash_prefix(self):
        """Each criterion line starts with '- Criterio:'."""
        criteria = [
            EvaluationCriterion(name="Test", description="Desc", weight=2.0)
        ]
        result = format_rubric_text(criteria)
        lines = [line for line in result.splitlines() if line.strip()]
        # The first content line should begin with "- "
        assert lines[0].startswith("- ")

    def test_description_on_indented_line(self):
        """The description appears on a line indented with spaces."""
        criteria = [
            EvaluationCriterion(name="Test", description="My description", weight=1.0)
        ]
        result = format_rubric_text(criteria)
        desc_lines = [line for line in result.splitlines() if "My description" in line]
        assert len(desc_lines) == 1
        assert desc_lines[0].startswith("  ")


# ---------------------------------------------------------------------------
# format_rag_context
# ---------------------------------------------------------------------------

class TestFormatRagContext:

    def test_single_context(self):
        """A single context chunk is numbered [TRECHO 1]."""
        contexts = [
            RetrievedContext(
                content="Arvore AVL mantem balanceamento.",
                source_document="slides.pdf",
                page_number=10,
                relevance_score=0.9,
            )
        ]
        result = format_rag_context(contexts)
        assert "[TRECHO 1]" in result
        assert "slides.pdf" in result
        assert "10" in result
        assert "Arvore AVL mantem balanceamento." in result

    def test_multiple_contexts(self, sample_rag_context):
        """Multiple contexts are numbered sequentially."""
        result = format_rag_context(sample_rag_context)
        assert "[TRECHO 1]" in result
        assert "[TRECHO 2]" in result
        assert sample_rag_context[0].source_document in result
        assert sample_rag_context[1].source_document in result

    def test_empty_list_returns_empty_string(self):
        """An empty context list produces an empty string."""
        result = format_rag_context([])
        assert result == ""

    def test_page_number_included(self):
        """The page number appears in the formatted header."""
        contexts = [
            RetrievedContext(
                content="Content here",
                source_document="book.pdf",
                page_number=42,
                relevance_score=0.7,
            )
        ]
        result = format_rag_context(contexts)
        assert "42" in result

    def test_none_page_number_shown(self):
        """When page_number is None, it still renders (as 'None')."""
        contexts = [
            RetrievedContext(
                content="Content",
                source_document="doc.pdf",
                relevance_score=0.6,
            )
        ]
        result = format_rag_context(contexts)
        # page_number=None renders in the f-string
        assert "None" in result

    def test_content_preserved_verbatim(self):
        """The full content string appears in the output without truncation."""
        long_content = "A" * 500
        contexts = [
            RetrievedContext(
                content=long_content,
                source_document="big.pdf",
                page_number=1,
                relevance_score=0.5,
            )
        ]
        result = format_rag_context(contexts)
        assert long_content in result
