"""
Controller para buscar estatísticas de uma prova corrigida.
"""

from uuid import UUID
from fastapi import HTTPException

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.services.results.results_service import ResultsService

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


logger = get_logger(__name__)


class GetExamResultsController(ControllerInterface):
    """
    Controller para retornar estatísticas de uma prova corrigida.
    """
    
    def __init__(self, service: ResultsService) -> None:
        self.__service = service
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa requisição para buscar resultados/estatísticas da prova.
        
        Args:
            http_request: Requisição HTTP contendo exam_uuid no param
            
        Returns:
            HttpResponse com ExamResultsResponse
            
        Raises:
            HTTPException: Em caso de erro
        """
        
        logger.info(
            "Handling get exam results request from caller: %s - %s",
            http_request.caller.ip,
            http_request.caller.user_agent
        )
        
        try:
            exam_uuid_str = http_request.param.get("exam_uuid")
            if not exam_uuid_str:
                raise ValueError("exam_uuid é obrigatório")
            
            exam_uuid = UUID(exam_uuid_str)
            
            results = self.__service.get_exam_results(
                db=http_request.db,
                exam_uuid=exam_uuid
            )
            
            logger.info("Exam results retrieved successfully: %s", exam_uuid)
            
            return HttpResponse(
                status_code=200,
                body=results
            )
            
        except NotFoundError as e:
            logger.warning("Exam not found: %s", str(e))
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            logger.error("Invalid data: %s", str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e
        except ValidateError as e:
            logger.warning("Validation error: %s", str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            logger.exception("Unexpected error getting exam results")
            raise HTTPException(status_code=500, detail="Internal server error") from e
