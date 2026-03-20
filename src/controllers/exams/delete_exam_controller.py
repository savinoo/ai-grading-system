from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exams.delete_exam_service import DeleteExamService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class DeleteExamController(ControllerInterface):
    """  
    Controller que delega ao DeleteExamService a exclusão de uma prova.
    """

    def __init__(self, service: DeleteExamService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de exclusão de prova.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP com status 204 (No Content)
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller
        token_infos = http_request.token_infos

        self.__logger.debug(
            "Handling delete exam request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        # Extrai exam_uuid do path param
        exam_uuid_str = http_request.param.get("exam_uuid")
        if not exam_uuid_str:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID da prova não fornecido"}
            )

        # Extrai teacher_uuid do token
        teacher_uuid_str = token_infos.get("sub")
        if not teacher_uuid_str:
            raise HTTPException(
                status_code=401,
                detail={"error": "Token inválido: professor não identificado"}
            )

        try:
            exam_uuid = UUID(exam_uuid_str)
            teacher_uuid = UUID(teacher_uuid_str)
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID inválido"}
            ) from ve

        try:
            asyncio.run(self.__service.delete_exam(db, exam_uuid, teacher_uuid))

            self.__logger.info("Prova deletada com sucesso: %s", exam_uuid)

            return HttpResponse(
                status_code=204,
                body=None
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao deletar prova: %s", val_err.message)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao deletar prova: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao deletar prova",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error("Erro inesperado ao deletar prova: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno do servidor"}
            ) from e
