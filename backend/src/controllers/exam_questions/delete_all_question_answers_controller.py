from __future__ import annotations

import asyncio
from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_questions.delete_all_question_answers_service import DeleteAllQuestionAnswersService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class DeleteAllQuestionAnswersController(ControllerInterface):
    """  
    Controller que delega ao DeleteAllQuestionAnswersService a remoção de todas as respostas de uma questão.
    """

    def __init__(self, service: DeleteAllQuestionAnswersService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de remoção de todas as respostas de uma questão.
        
        Args:
            http_request: Requisição HTTP contendo o UUID da questão
            
        Returns:
            HttpResponse: Resposta HTTP com o número de respostas removidas
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller
        question_uuid: UUID = http_request.path_params.get("question_uuid")

        self.__logger.debug(
            "Handling delete all question answers request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            deleted_count = asyncio.run(self.__service.delete_all_question_answers(db, question_uuid))

            self.__logger.info(
                "Respostas da questão removidas com sucesso: %s (%d respostas)",
                question_uuid,
                deleted_count
            )

            return HttpResponse(
                status_code=200,
                body={"deleted_count": deleted_count, "message": f"{deleted_count} respostas removidas"}
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao remover respostas: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao remover respostas: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao remover respostas da questão",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao remover respostas")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
