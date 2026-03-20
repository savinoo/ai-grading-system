from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_criteria.list_exam_criteria_service import ListExamCriteriaService

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class ListExamCriteriaController(ControllerInterface):
    """  
    Controller que delega ao ListExamCriteriaService a listagem de critérios de uma prova.
    """

    def __init__(self, service: ListExamCriteriaService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de listagem de critérios de prova.
        
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
            "Handling list exam criteria request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            exam_uuid = UUID(params.get("exam_uuid"))
            skip = params.get("skip", 0)
            limit = params.get("limit", 100)
            active_only = params.get("active_only", True)

            result = asyncio.run(
                self.__service.list_exam_criteria(
                    db,
                    exam_uuid,
                    skip=skip,
                    limit=limit,
                    active_only=active_only
                )
            )

            self.__logger.info("Listados %d critérios da prova %s", len(result), exam_uuid)

            return HttpResponse(
                status_code=200,
                body={"data": result, "total": len(result)}
            )

        except ValueError as val_err:
            self.__logger.warning("UUID inválido: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID inválido"}
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao listar critérios: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao listar critérios da prova",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error("Erro inesperado ao listar critérios: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno do servidor"}
            ) from e
