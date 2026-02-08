from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.student_answers.update_student_answer_service import UpdateStudentAnswerService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class UpdateStudentAnswerController(ControllerInterface):
    """  
    Controller que delega ao UpdateStudentAnswerService a atualização de resposta de aluno.
    """

    def __init__(self, service: UpdateStudentAnswerService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de atualização de resposta de aluno.
        
        Args:
            http_request: Requisição HTTP contendo os dados da resposta
            
        Returns:
            HttpResponse: Resposta HTTP com os dados da resposta atualizada
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller
        answer_uuid: UUID = http_request.path_params.get("answer_uuid")

        self.__logger.debug(
            "Handling update student answer request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            request = http_request.body

            result = asyncio.run(self.__service.update_student_answer(db, answer_uuid, request))

            self.__logger.info("Resposta de aluno atualizada com sucesso: %s", result.uuid)

            return HttpResponse(
                status_code=200,
                body=result
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao atualizar resposta: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao atualizar resposta: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao atualizar resposta de aluno",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao atualizar resposta")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
