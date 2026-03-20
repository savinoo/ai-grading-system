from src.models.repositories.grading_criteria_repository import GradingCriteriaRepository

from src.services.grading_criteria.list_grading_criteria_service import ListGradingCriteriaService

from src.controllers.grading_criteria.list_grading_criteria_controller import ListGradingCriteriaController

def make_list_grading_criteria_controller() -> ListGradingCriteriaController:
    """
    Factory para criar uma instância de ListGradingCriteriaController
    com suas dependências injetadas.
    
    Returns:
        ListGradingCriteriaController: Instância do controlador de listagem de critérios de avaliação
    """
    grading_criteria_repository = GradingCriteriaRepository()
    list_service = ListGradingCriteriaService(grading_criteria_repository)
    controller = ListGradingCriteriaController(list_service)

    return controller
