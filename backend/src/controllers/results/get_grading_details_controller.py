"""
Controller para buscar detalhes de correção de uma resposta.
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


class GetGradingDetailsController(ControllerInterface):
    """
    Controller para retornar detalhes completos da correção de uma resposta.
    """
    
    def __init__(self, service: ResultsService) -> None:
        self.__service = service
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa requisição para buscar detalhes de correção.
        
        Args:
            http_request: Requisição HTTP contendo answer_uuid no param
            
        Returns:
            HttpResponse com GradingDetailsResponse
            
        Raises:
            HTTPException: Em caso de erro
        """
        
        logger.info(
            "Handling get grading details request from caller: %s - %s",
            http_request.caller.ip,
            http_request.caller.user_agent
        )
        
        try:
            answer_uuid_str = http_request.param.get("answer_uuid")
            if not answer_uuid_str:
                raise ValueError("answer_uuid é obrigatório")
            
            answer_uuid = UUID(answer_uuid_str)
            
            details = self.__service.get_grading_details(
                db=http_request.db,
                answer_uuid=answer_uuid
            )
            
            logger.info("Grading details retrieved successfully: %s", answer_uuid)
            
            return HttpResponse(
                status_code=200,
                body=details
            )
            
        except NotFoundError as e:
            logger.warning("Answer not found: %s", str(e))
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            logger.error("Invalid data: %s", str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e
        except ValidateError as e:
            logger.warning("Validation error: %s", str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            logger.exception("Unexpected error getting grading details")
            raise HTTPException(status_code=500, detail="Internal server error") from e
