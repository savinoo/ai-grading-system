from __future__ import annotations

import asyncio
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.student_answers.create_student_answer_service import CreateStudentAnswerService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class CreateStudentAnswerController(ControllerInterface):
    """  
    Controller que delega ao CreateStudentAnswerService a criação de resposta de aluno.
    """

    def __init__(self, service: CreateStudentAnswerService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de criação de resposta de aluno.
        
        Args:
            http_request: Requisição HTTP contendo os dados da resposta
            
        Returns:
            HttpResponse: Resposta HTTP com os dados da resposta criada
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller

        self.__logger.debug(
            "Handling create student answer request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            request = http_request.body

            result = asyncio.run(self.__service.create_student_answer(db, request))

            self.__logger.info("Resposta de aluno criada com sucesso: %s", result.uuid)

            return HttpResponse(
                status_code=201,
                body=result
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao criar resposta: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao criar resposta: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao criar resposta de aluno",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao criar resposta")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
