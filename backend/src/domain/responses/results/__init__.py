"""
Responses para funcionalidades de resultados de correção.
"""

from .exam_results_response import (
    ExamResultsResponse,
    ExamStatistics,
    QuestionStatistics,
    ScoreDistribution
)
from .grading_details_response import (
    GradingDetailsResponse,
    StudentInfo,
    QuestionInfo,
    CriterionScoreDetail,
    CriterionScoreSimple,
    AgentCorrectionDetail,
    RAGContextItem,
    AgentScoreBreakdown
)
from .exams_list_response import ExamResultsSummaryResponse

__all__ = [
    "ExamResultsResponse",
    "ExamStatistics",
    "QuestionStatistics",
    "ScoreDistribution",
    "GradingDetailsResponse",
    "StudentInfo",
    "QuestionInfo",
    "CriterionScoreDetail",
    "CriterionScoreSimple",
    "AgentCorrectionDetail",
    "RAGContextItem",
    "AgentScoreBreakdown",
    "ExamResultsSummaryResponse"
]
