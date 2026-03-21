"""Controllers para gerenciamento de respostas de alunos."""
from src.controllers.student_answers.create_student_answer_controller import CreateStudentAnswerController
from src.controllers.student_answers.update_student_answer_controller import UpdateStudentAnswerController
from src.controllers.student_answers.delete_student_answer_controller import DeleteStudentAnswerController

__all__ = [
    "CreateStudentAnswerController",
    "UpdateStudentAnswerController",
    "DeleteStudentAnswerController"
]
