"""
Controller para listar provas com resultados.
"""

from fastapi import HTTPException

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.services.results.results_service import ResultsService

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


logger = get_logger(__name__)


class ListExamsResultsController(ControllerInterface):
    """
    Controller para retornar lista de provas com resultados disponíveis.
    """
    
    def __init__(self, service: ResultsService) -> None:
        self.__service = service
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa requisição para listar provas com resultados.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse com lista de ExamResultsSummaryResponse
            
        Raises:
            HTTPException: Em caso de erro
        """
        
        logger.info(
            "Handling list exams results request from caller: %s - %s",
            http_request.caller.ip,
            http_request.caller.user_agent
        )
        
        try:
            user_uuid = http_request.token_infos.get("sub")
            if not user_uuid:
                raise ValueError("user_uuid não encontrado no token")
            
            exams_list = self.__service.list_exams_results(
                db=http_request.db,
                user_uuid=user_uuid
            )
            
            logger.info("Listed %d exams with results for user %s", len(exams_list), user_uuid)
            
            return HttpResponse(
                status_code=200,
                body=exams_list
            )
            
        except ValueError as e:
            logger.error("Invalid data: %s", str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e
        except ValidateError as e:
            logger.warning("Validation error: %s", str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            logger.exception("Unexpected error listing exams results")
            raise HTTPException(status_code=500, detail="Internal server error") from e
