"""Interfaces para serviços de questões de prova."""
from src.interfaces.services.exam_questions.create_exam_question_service_interface import CreateExamQuestionServiceInterface
from src.interfaces.services.exam_questions.delete_exam_question_service_interface import DeleteExamQuestionServiceInterface
from src.interfaces.services.exam_questions.delete_all_question_answers_service_interface import DeleteAllQuestionAnswersServiceInterface
from src.interfaces.services.exam_questions.update_exam_question_service_interface import UpdateExamQuestionServiceInterface

__all__ = [
    "CreateExamQuestionServiceInterface",
    "DeleteExamQuestionServiceInterface",
    "DeleteAllQuestionAnswersServiceInterface",
    "UpdateExamQuestionServiceInterface"
]
