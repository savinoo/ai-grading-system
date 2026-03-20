from src.models.repositories.student_answer_repository import StudentAnswerRepository
from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.student_repository import StudentRepository

from src.services.student_answers.create_student_answer_service import CreateStudentAnswerService
from src.services.student_answers.update_student_answer_service import UpdateStudentAnswerService
from src.services.student_answers.delete_student_answer_service import DeleteStudentAnswerService
from src.services.student_answers.list_student_answers_service import ListStudentAnswersService

from src.controllers.student_answers.create_student_answer_controller import CreateStudentAnswerController
from src.controllers.student_answers.update_student_answer_controller import UpdateStudentAnswerController
from src.controllers.student_answers.delete_student_answer_controller import DeleteStudentAnswerController
from src.controllers.student_answers.list_student_answers_controller import ListStudentAnswersController

def make_create_student_answer_controller() -> CreateStudentAnswerController:
    """
    Factory para criar uma instância de CreateStudentAnswerController
    com suas dependências injetadas.
    
    Returns:
        CreateStudentAnswerController: Instância do controlador de criação de resposta
    """
    student_answer_repository = StudentAnswerRepository()
    question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    student_repository = StudentRepository()
    
    create_service = CreateStudentAnswerService(
        student_answer_repository,
        question_repository,
        exams_repository,
        student_repository
    )
    controller = CreateStudentAnswerController(create_service)

    return controller

def make_update_student_answer_controller() -> UpdateStudentAnswerController:
    """
    Factory para criar uma instância de UpdateStudentAnswerController
    com suas dependências injetadas.
    
    Returns:
        UpdateStudentAnswerController: Instância do controlador de atualização de resposta
    """
    student_answer_repository = StudentAnswerRepository()
    question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    
    update_service = UpdateStudentAnswerService(
        student_answer_repository,
        question_repository,
        exams_repository
    )
    controller = UpdateStudentAnswerController(update_service)

    return controller

def make_delete_student_answer_controller() -> DeleteStudentAnswerController:
    """
    Factory para criar uma instância de DeleteStudentAnswerController
    com suas dependências injetadas.
    
    Returns:
        DeleteStudentAnswerController: Instância do controlador de remoção de resposta
    """
    student_answer_repository = StudentAnswerRepository()
    question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    
    delete_service = DeleteStudentAnswerService(
        student_answer_repository,
        question_repository,
        exams_repository
    )
    controller = DeleteStudentAnswerController(delete_service)

    return controller

def make_list_student_answers_controller() -> ListStudentAnswersController:
    """
    Factory para criar uma instância de ListStudentAnswersController
    com suas dependências injetadas.
    
    Returns:
        ListStudentAnswersController: Instância do controlador de listagem de respostas
    """
    student_answer_repository = StudentAnswerRepository()
    question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    
    list_service = ListStudentAnswersService(
        student_answer_repository,
        question_repository,
        exams_repository
    )
    controller = ListStudentAnswersController(list_service)

    return controller
