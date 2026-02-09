from __future__ import annotations

import asyncio
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.student_answers.list_student_answers_service import ListStudentAnswersService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


class ListStudentAnswersController(ControllerInterface):
    """
    Controller que delega ao ListStudentAnswersService a listagem de respostas de alunos.
    """

    def __init__(self, service: ListStudentAnswersService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de listagem de respostas de alunos.
        
        Args:
            http_request: Requisição HTTP contendo parâmetros da listagem
            
        Returns:
            HttpResponse: Resposta HTTP com lista de respostas
            
        Raises:
            HTTPException: Em caso de erro
        """
        db = http_request.db
        caller = http_request.caller

        self.__logger.debug(
            "Handling list student answers request from caller: %s - %s - %s",
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            # Extrair parâmetros
            question_uuid = http_request.param.get("question_uuid")
            teacher_uuid = http_request.token_infos.get("sub")

            if not question_uuid:
                raise HTTPException(
                    status_code=400,
                    detail="Parâmetro 'question_uuid' é obrigatório"
                )

            if not teacher_uuid:
                raise HTTPException(
                    status_code=401,
                    detail="Usuário não autenticado"
                )

            # Executar serviço
            student_answers = asyncio.run(
                self.__service.list_student_answers(
                    db=db,
                    question_uuid=question_uuid,
                    teacher_uuid=teacher_uuid
                )
            )

            self.__logger.info("Listadas %d respostas da questão %s", len(student_answers), question_uuid)

            return HttpResponse(
                status_code=200,
                body=student_answers
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao listar respostas: %s", val_err)
            raise HTTPException(
                status_code=400 if "não encontrada" in val_err.message else 403,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao listar respostas: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao listar respostas",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao listar respostas")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
