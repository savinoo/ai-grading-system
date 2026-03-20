"""Interfaces para serviços de respostas de alunos."""
from src.interfaces.services.student_answers.create_student_answer_service_interface import CreateStudentAnswerServiceInterface
from src.interfaces.services.student_answers.update_student_answer_service_interface import UpdateStudentAnswerServiceInterface
from src.interfaces.services.student_answers.delete_student_answer_service_interface import DeleteStudentAnswerServiceInterface

__all__ = [
    "CreateStudentAnswerServiceInterface",
    "UpdateStudentAnswerServiceInterface",
    "DeleteStudentAnswerServiceInterface"
]
