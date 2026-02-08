from __future__ import annotations

import asyncio
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_questions.list_exam_questions_service import ListExamQuestionsService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


class ListExamQuestionsController(ControllerInterface):
    """
    Controller que delega ao ListExamQuestionsService a listagem de questões.
    """

    def __init__(self, service: ListExamQuestionsService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de listagem de questões.
        
        Args:
            http_request: Requisição HTTP contendo parâmetros da listagem
            
        Returns:
            HttpResponse: Resposta HTTP com lista de questões
            
        Raises:
            HTTPException: Em caso de erro
        """
        db = http_request.db
        caller = http_request.caller

        self.__logger.debug(
            "Handling list exam questions request from caller: %s - %s - %s",
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            # Extrair parâmetros
            exam_uuid = http_request.param.get("exam_uuid")
            teacher_uuid = http_request.token_infos.get("sub")

            if not exam_uuid:
                raise HTTPException(
                    status_code=400,
                    detail="Parâmetro 'exam_uuid' é obrigatório"
                )

            if not teacher_uuid:
                raise HTTPException(
                    status_code=401,
                    detail="Usuário não autenticado"
                )

            # Executar serviço
            questions = asyncio.run(
                self.__service.list_exam_questions(
                    db=db,
                    exam_uuid=exam_uuid,
                    teacher_uuid=teacher_uuid
                )
            )

            self.__logger.info("Listadas %d questões da prova %s", len(questions), exam_uuid)

            return HttpResponse(
                status_code=200,
                body=questions
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao listar questões: %s", val_err)
            raise HTTPException(
                status_code=400 if "não encontrada" in val_err.message else 403,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao listar questões: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao listar questões",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao listar questões")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e

