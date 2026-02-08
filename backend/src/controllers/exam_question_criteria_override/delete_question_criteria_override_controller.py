from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_question_criteria_override.delete_question_criteria_override_service import (
    DeleteQuestionCriteriaOverrideService,
)

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class DeleteQuestionCriteriaOverrideController(ControllerInterface):
    """  
    Controller que delega ao DeleteQuestionCriteriaOverrideService a remoção de sobrescrita.
    """

    def __init__(self, service: DeleteQuestionCriteriaOverrideService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de remoção de sobrescrita.
        """

        db = http_request.db
        caller = http_request.caller
        override_uuid: UUID = http_request.path_params.get("override_uuid")

        self.__logger.debug(
            "Handling delete criteria override request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            asyncio.run(self.__service.delete_question_criteria_override(db, override_uuid))

            self.__logger.info("Sobrescrita removida com sucesso: %s", override_uuid)

            return HttpResponse(
                status_code=204,
                body=None
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao remover sobrescrita: %s", val_err)
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
                "Erro de banco de dados ao remover sobrescrita: %s",
                sql_err,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao remover sobrescrita",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao remover sobrescrita")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
