from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exams.update_exam_service import UpdateExamService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.not_found import NotFoundError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class UpdateExamController(ControllerInterface):
    """  
    Controller que delega ao UpdateExamService a atualização de uma prova.
    """

    def __init__(self, service: UpdateExamService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de atualização de prova.
        
        Args:
            http_request: Requisição HTTP contendo os dados da prova
            
        Returns:
            HttpResponse: Resposta HTTP com os dados da prova atualizada
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller

        self.__logger.debug(
            "Handling update exam request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        exam_uuid_str = http_request.param.get("exam_uuid")
        if not exam_uuid_str:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID da prova não fornecido"}
            )

        try:
            exam_uuid = UUID(exam_uuid_str)
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID da prova inválido"}
            ) from ve

        request = http_request.body

        try:
            result = asyncio.run(self.__service.update_exam(db, exam_uuid, request))

            self.__logger.info("Prova atualizada com sucesso: %s", exam_uuid)

            return HttpResponse(
                status_code=200,
                body=result
            )

        except NotFoundError as nf_err:
            self.__logger.warning("Prova não encontrada: %s", exam_uuid)
            raise HTTPException(
                status_code=404,
                detail={
                    "error": nf_err.message,
                    "code": nf_err.code
                }
            ) from nf_err

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao atualizar prova: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao atualizar prova: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao atualizar prova",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error("Erro inesperado ao atualizar prova: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno ao atualizar prova"}
            ) from e
