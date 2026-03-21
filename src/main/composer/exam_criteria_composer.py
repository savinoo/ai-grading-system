from src.models.repositories.exam_criteria_repository import ExamCriteriaRepository
from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.grading_criteria_repository import GradingCriteriaRepository

from src.services.exam_criteria.create_exam_criteria_service import CreateExamCriteriaService
from src.services.exam_criteria.list_exam_criteria_service import ListExamCriteriaService
from src.services.exam_criteria.update_exam_criteria_service import UpdateExamCriteriaService
from src.services.exam_criteria.delete_exam_criteria_service import DeleteExamCriteriaService

from src.controllers.exam_criteria.create_exam_criteria_controller import CreateExamCriteriaController
from src.controllers.exam_criteria.list_exam_criteria_controller import ListExamCriteriaController
from src.controllers.exam_criteria.update_exam_criteria_controller import UpdateExamCriteriaController
from src.controllers.exam_criteria.delete_exam_criteria_controller import DeleteExamCriteriaController

def make_create_exam_criteria_controller() -> CreateExamCriteriaController:
    """
    Factory para criar uma instância de CreateExamCriteriaController
    com suas dependências injetadas.
    
    Returns:
        CreateExamCriteriaController: Instância do controlador de criação de critério de prova
    """
    exam_criteria_repository = ExamCriteriaRepository()
    exams_repository = ExamsRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    
    create_service = CreateExamCriteriaService(
        exam_criteria_repository,
        exams_repository,
        grading_criteria_repository
    )
    controller = CreateExamCriteriaController(create_service)

    return controller

def make_list_exam_criteria_controller() -> ListExamCriteriaController:
    """
    Factory para criar uma instância de ListExamCriteriaController
    com suas dependências injetadas.
    
    Returns:
        ListExamCriteriaController: Instância do controlador de listagem de critérios de prova
    """
    exam_criteria_repository = ExamCriteriaRepository()
    list_service = ListExamCriteriaService(exam_criteria_repository)
    controller = ListExamCriteriaController(list_service)

    return controller

def make_update_exam_criteria_controller() -> UpdateExamCriteriaController:
    """
    Factory para criar uma instância de UpdateExamCriteriaController
    com suas dependências injetadas.
    
    Returns:
        UpdateExamCriteriaController: Instância do controlador de atualização de critério de prova
    """
    exam_criteria_repository = ExamCriteriaRepository()
    exams_repository = ExamsRepository()
    
    update_service = UpdateExamCriteriaService(
        exam_criteria_repository,
        exams_repository
    )
    controller = UpdateExamCriteriaController(update_service)

    return controller

def make_delete_exam_criteria_controller() -> DeleteExamCriteriaController:
    """
    Factory para criar uma instância de DeleteExamCriteriaController
    com suas dependências injetadas.
    
    Returns:
        DeleteExamCriteriaController: Instância do controlador de remoção de critério de prova
    """
    exam_criteria_repository = ExamCriteriaRepository()
    exams_repository = ExamsRepository()
    
    delete_service = DeleteExamCriteriaService(
        exam_criteria_repository,
        exams_repository
    )
    controller = DeleteExamCriteriaController(delete_service)

    return controller
