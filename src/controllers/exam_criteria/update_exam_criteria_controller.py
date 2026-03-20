from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_criteria.update_exam_criteria_service import UpdateExamCriteriaService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class UpdateExamCriteriaController(ControllerInterface):
    """  
    Controller que delega ao UpdateExamCriteriaService a atualização de critério de prova.
    """

    def __init__(self, service: UpdateExamCriteriaService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de atualização de critério de prova.
        
        Args:
            http_request: Requisição HTTP contendo os dados a atualizar
            
        Returns:
            HttpResponse: Resposta HTTP com os dados do critério atualizado
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller
        params = http_request.param or {}

        self.__logger.debug(
            "Handling update exam criteria request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            exam_criteria_uuid = UUID(params.get("exam_criteria_uuid"))
            request = http_request.body

            result = asyncio.run(
                self.__service.update_exam_criteria(db, exam_criteria_uuid, request)
            )

            self.__logger.info("Critério de prova atualizado com sucesso: %s", exam_criteria_uuid)

            return HttpResponse(
                status_code=200,
                body=result
            )

        except ValueError as val_err:
            self.__logger.warning("UUID inválido: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID inválido"}
            ) from val_err

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao atualizar critério: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao atualizar critério: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao atualizar critério de prova",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error("Erro inesperado ao atualizar critério: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno do servidor"}
            ) from e
