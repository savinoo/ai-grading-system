"""Requests para operações com questões de prova."""
from src.domain.requests.exam_questions.exam_question_create_request import ExamQuestionCreateRequest
from src.domain.requests.exam_questions.exam_question_update_request import ExamQuestionUpdateRequest

__all__ = [
    "ExamQuestionCreateRequest",
    "ExamQuestionUpdateRequest"
]
