from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_question_criteria_override.update_question_criteria_override_service import (
    UpdateQuestionCriteriaOverrideService,
)

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class UpdateQuestionCriteriaOverrideController(ControllerInterface):
    """  
    Controller que delega ao UpdateQuestionCriteriaOverrideService a atualização de sobrescrita.
    """

    def __init__(self, service: UpdateQuestionCriteriaOverrideService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de atualização de sobrescrita.
        """

        db = http_request.db
        caller = http_request.caller
        override_uuid: UUID = http_request.path_params.get("override_uuid")

        self.__logger.debug(
            "Handling update criteria override request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            request = http_request.body

            result = asyncio.run(
                self.__service.update_question_criteria_override(db, override_uuid, request)
            )

            self.__logger.info("Sobrescrita atualizada com sucesso: %s", result.uuid)

            return HttpResponse(
                status_code=200,
                body=result
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao atualizar sobrescrita: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error(
                "Erro de banco de dados ao atualizar sobrescrita: %s",
                sql_err,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao atualizar sobrescrita",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao atualizar sobrescrita")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
