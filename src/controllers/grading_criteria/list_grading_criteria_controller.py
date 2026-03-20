from __future__ import annotations

import asyncio
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.grading_criteria.list_grading_criteria_service import ListGradingCriteriaService

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class ListGradingCriteriaController(ControllerInterface):
    """  
    Controller que delega ao ListGradingCriteriaService a listagem de critérios de avaliação.
    """

    def __init__(self, service: ListGradingCriteriaService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de listagem de critérios de avaliação.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP com a lista de critérios
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller
        params = http_request.param or {}

        self.__logger.debug(
            "Handling list grading criteria request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            skip = params.get("skip", 0)
            limit = params.get("limit", 100)
            active_only = params.get("active_only", True)

            result = asyncio.run(
                self.__service.list_grading_criteria(
                    db,
                    skip=skip,
                    limit=limit,
                    active_only=active_only
                )
            )

            self.__logger.info("Listados %d critérios de avaliação", len(result))

            return HttpResponse(
                status_code=200,
                body={"data": result, "total": len(result)}
            )

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao listar critérios: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao listar critérios de avaliação",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error("Erro inesperado ao listar critérios: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno do servidor"}
            ) from e
