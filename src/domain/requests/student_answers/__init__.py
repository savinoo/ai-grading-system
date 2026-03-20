"""Requests para operações com respostas de alunos."""
from src.domain.requests.student_answers.student_answer_create_request import StudentAnswerCreateRequest
from src.domain.requests.student_answers.student_answer_update_request import StudentAnswerUpdateRequest

__all__ = [
    "StudentAnswerCreateRequest",
    "StudentAnswerUpdateRequest"
]
