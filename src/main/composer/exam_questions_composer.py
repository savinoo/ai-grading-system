from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.student_answer_repository import StudentAnswerRepository

from src.services.exam_questions.create_exam_question_service import CreateExamQuestionService
from src.services.exam_questions.delete_exam_question_service import DeleteExamQuestionService
from src.services.exam_questions.delete_all_question_answers_service import DeleteAllQuestionAnswersService
from src.services.exam_questions.list_exam_questions_service import ListExamQuestionsService
from src.services.exam_questions.update_exam_question_service import UpdateExamQuestionService

from src.controllers.exam_questions.create_exam_question_controller import CreateExamQuestionController
from src.controllers.exam_questions.delete_exam_question_controller import DeleteExamQuestionController
from src.controllers.exam_questions.delete_all_question_answers_controller import DeleteAllQuestionAnswersController
from src.controllers.exam_questions.list_exam_questions_controller import ListExamQuestionsController
from src.controllers.exam_questions.update_exam_question_controller import UpdateExamQuestionController

def make_create_exam_question_controller() -> CreateExamQuestionController:
    """
    Factory para criar uma instância de CreateExamQuestionController
    com suas dependências injetadas.
    
    Returns:
        CreateExamQuestionController: Instância do controlador de criação de questão
    """
    exam_question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    
    create_service = CreateExamQuestionService(
        exam_question_repository,
        exams_repository
    )
    controller = CreateExamQuestionController(create_service)

    return controller

def make_delete_exam_question_controller() -> DeleteExamQuestionController:
    """
    Factory para criar uma instância de DeleteExamQuestionController
    com suas dependências injetadas.
    
    Returns:
        DeleteExamQuestionController: Instância do controlador de remoção de questão
    """
    exam_question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    
    delete_service = DeleteExamQuestionService(
        exam_question_repository,
        exams_repository
    )
    controller = DeleteExamQuestionController(delete_service)

    return controller

def make_delete_all_question_answers_controller() -> DeleteAllQuestionAnswersController:
    """
    Factory para criar uma instância de DeleteAllQuestionAnswersController
    com suas dependências injetadas.
    
    Returns:
        DeleteAllQuestionAnswersController: Instância do controlador de remoção de respostas
    """
    exam_question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    
    delete_service = DeleteAllQuestionAnswersService(
        exam_question_repository,
        exams_repository,
        student_answer_repository
    )
    controller = DeleteAllQuestionAnswersController(delete_service)

    return controller

def make_list_exam_questions_controller() -> ListExamQuestionsController:
    """
    Factory para criar uma instância de ListExamQuestionsController
    com suas dependências injetadas.
    
    Returns:
        ListExamQuestionsController: Instância do controlador de listagem de questões
    """
    exam_question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    
    list_service = ListExamQuestionsService(
        exam_question_repository,
        exams_repository
    )
    controller = ListExamQuestionsController(list_service)

    return controller

def make_update_exam_question_controller() -> UpdateExamQuestionController:
    """
    Factory para criar uma instância de UpdateExamQuestionController
    com suas dependências injetadas.
    
    Returns:
        UpdateExamQuestionController: Instância do controlador de atualização de questão
    """
    exam_question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    
    update_service = UpdateExamQuestionService(
        exam_question_repository,
        exams_repository
    )
    controller = UpdateExamQuestionController(update_service)

    return controller
