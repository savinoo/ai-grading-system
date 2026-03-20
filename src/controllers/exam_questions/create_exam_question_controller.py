from __future__ import annotations

import asyncio
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_questions.create_exam_question_service import CreateExamQuestionService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class CreateExamQuestionController(ControllerInterface):
    """  
    Controller que delega ao CreateExamQuestionService a criação de questão de prova.
    """

    def __init__(self, service: CreateExamQuestionService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de criação de questão de prova.
        
        Args:
            http_request: Requisição HTTP contendo os dados da questão
            
        Returns:
            HttpResponse: Resposta HTTP com os dados da questão criada
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller

        self.__logger.debug(
            "Handling create exam question request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            request = http_request.body

            result = asyncio.run(self.__service.create_exam_question(db, request))

            self.__logger.info("Questão de prova criada com sucesso: %s", result.uuid)

            return HttpResponse(
                status_code=201,
                body=result
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao criar questão: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao criar questão: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao criar questão de prova",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao criar questão")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
