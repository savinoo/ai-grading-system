from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_questions.update_exam_question_service import UpdateExamQuestionService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class UpdateExamQuestionController(ControllerInterface):
    """  
    Controller que delega ao UpdateExamQuestionService a atualização de questões.
    """

    def __init__(self, service: UpdateExamQuestionService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de atualização de questão.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP com os dados da questão atualizada
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller
        token_infos = http_request.token_infos
        body = http_request.body

        self.__logger.debug(
            "Handling update exam question request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        question_uuid_str = http_request.param.get("question_uuid")
        if not question_uuid_str:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID da questão não fornecido"}
            )

        teacher_uuid_str = token_infos.get("sub")
        if not teacher_uuid_str:
            raise HTTPException(
                status_code=401,
                detail={"error": "Token inválido: professor não identificado"}
            )

        try:
            question_uuid = UUID(question_uuid_str)
            teacher_uuid = UUID(teacher_uuid_str)
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID inválido"}
            ) from ve

        try:
            result = asyncio.run(
                self.__service.update_exam_question(
                    db,
                    question_uuid,
                    teacher_uuid,
                    body
                )
            )

            self.__logger.info("Questão atualizada com sucesso: %s", question_uuid)

            return HttpResponse(
                status_code=200,
                body=result
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao atualizar questão: %s", val_err.message)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao atualizar questão: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao atualizar questão",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error("Erro inesperado ao atualizar questão: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno do servidor"}
            ) from e
