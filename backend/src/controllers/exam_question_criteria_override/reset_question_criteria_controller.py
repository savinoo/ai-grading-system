from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_question_criteria_override.reset_question_criteria_service import ResetQuestionCriteriaService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class ResetQuestionCriteriaController(ControllerInterface):
    """  
    Controller que delega ao ResetQuestionCriteriaService o reset de critérios de uma questão.
    """

    def __init__(self, service: ResetQuestionCriteriaService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de reset de critérios de uma questão.
        
        Args:
            http_request: Requisição HTTP contendo o UUID da questão
            
        Returns:
            HttpResponse: Resposta HTTP com o número de sobrescritas removidas
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller
        question_uuid: UUID = http_request.path_params.get("question_uuid")

        self.__logger.debug(
            "Handling reset question criteria request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            deleted_count = asyncio.run(self.__service.reset_question_criteria(db, question_uuid))

            self.__logger.info(
                "Critérios da questão resetados com sucesso: %s (%d sobrescritas removidas)",
                question_uuid,
                deleted_count
            )

            return HttpResponse(
                status_code=200,
                body={"deleted_count": deleted_count, "message": f"Critérios resetados ({deleted_count} sobrescritas removidas)"}
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao resetar critérios: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao resetar critérios: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao resetar critérios",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao resetar critérios")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
