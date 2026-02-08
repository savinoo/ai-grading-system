from src.models.repositories.exam_question_criteria_override_repository import ExamQuestionCriteriaOverrideRepository
from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.grading_criteria_repository import GradingCriteriaRepository

from src.services.exam_question_criteria_override.create_question_criteria_override_service import CreateQuestionCriteriaOverrideService
from src.services.exam_question_criteria_override.reset_question_criteria_service import ResetQuestionCriteriaService
from src.services.exam_question_criteria_override.update_question_criteria_override_service import UpdateQuestionCriteriaOverrideService
from src.services.exam_question_criteria_override.delete_question_criteria_override_service import DeleteQuestionCriteriaOverrideService

from src.controllers.exam_question_criteria_override.create_question_criteria_override_controller import CreateQuestionCriteriaOverrideController
from src.controllers.exam_question_criteria_override.reset_question_criteria_controller import ResetQuestionCriteriaController
from src.controllers.exam_question_criteria_override.update_question_criteria_override_controller import UpdateQuestionCriteriaOverrideController
from src.controllers.exam_question_criteria_override.delete_question_criteria_override_controller import DeleteQuestionCriteriaOverrideController

def make_create_question_criteria_override_controller() -> CreateQuestionCriteriaOverrideController:
    """
    Factory para criar uma instância de CreateQuestionCriteriaOverrideController
    com suas dependências injetadas.
    
    Returns:
        CreateQuestionCriteriaOverrideController: Instância do controlador de criação de sobrescrita
    """
    override_repository = ExamQuestionCriteriaOverrideRepository()
    question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    
    create_service = CreateQuestionCriteriaOverrideService(
        override_repository,
        question_repository,
        exams_repository,
        grading_criteria_repository
    )
    controller = CreateQuestionCriteriaOverrideController(create_service)

    return controller

def make_reset_question_criteria_controller() -> ResetQuestionCriteriaController:
    """
    Factory para criar uma instância de ResetQuestionCriteriaController
    com suas dependências injetadas.
    
    Returns:
        ResetQuestionCriteriaController: Instância do controlador de reset de critérios
    """
    override_repository = ExamQuestionCriteriaOverrideRepository()
    question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()
    
    reset_service = ResetQuestionCriteriaService(
        override_repository,
        question_repository,
        exams_repository
    )
    controller = ResetQuestionCriteriaController(reset_service)

    return controller

def make_update_question_criteria_override_controller() -> UpdateQuestionCriteriaOverrideController:
    """
    Factory para criar uma instância de UpdateQuestionCriteriaOverrideController.
    """
    override_repository = ExamQuestionCriteriaOverrideRepository()
    question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()

    update_service = UpdateQuestionCriteriaOverrideService(
        override_repository,
        question_repository,
        exams_repository
    )
    controller = UpdateQuestionCriteriaOverrideController(update_service)

    return controller

def make_delete_question_criteria_override_controller() -> DeleteQuestionCriteriaOverrideController:
    """
    Factory para criar uma instância de DeleteQuestionCriteriaOverrideController.
    """
    override_repository = ExamQuestionCriteriaOverrideRepository()
    question_repository = ExamQuestionRepository()
    exams_repository = ExamsRepository()

    delete_service = DeleteQuestionCriteriaOverrideService(
        override_repository,
        question_repository,
        exams_repository
    )
    controller = DeleteQuestionCriteriaOverrideController(delete_service)

    return controller
