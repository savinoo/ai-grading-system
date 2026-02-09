from __future__ import annotations

import asyncio
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.services.exam_question_criteria_override.list_question_criteria_overrides_service import ListQuestionCriteriaOverridesService

from src.errors.domain.sql_error import SqlError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


class ListQuestionCriteriaOverridesController(ControllerInterface):
    """
    Controller que delega ao ListQuestionCriteriaOverridesService a listagem de critérios customizados.
    """

    def __init__(self, service: ListQuestionCriteriaOverridesService) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de listagem de critérios customizados.
        
        Args:
            http_request: Requisição HTTP contendo parâmetros da listagem
            
        Returns:
            HttpResponse: Resposta HTTP com lista de critérios customizados
            
        Raises:
            HTTPException: Em caso de erro
        """
        db = http_request.db
        caller = http_request.caller

        self.__logger.debug(
            "Handling list question criteria overrides request from caller: %s - %s - %s",
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
            criteria_overrides = asyncio.run(
                self.__service.list_question_criteria_overrides(
                    db=db,
                    question_uuid=question_uuid,
                    teacher_uuid=teacher_uuid
                )
            )

            self.__logger.info("Listados %d critérios customizados da questão %s", len(criteria_overrides), question_uuid)

            return HttpResponse(
                status_code=200,
                body=criteria_overrides
            )

        except ValidateError as val_err:
            self.__logger.warning("Erro de validação ao listar critérios customizados: %s", val_err)
            raise HTTPException(
                status_code=400 if "não encontrada" in val_err.message else 403,
                detail={
                    "error": val_err.message,
                    "code": val_err.code,
                    "context": val_err.context
                }
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao listar critérios customizados: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao listar critérios customizados",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.exception("Erro inesperado ao listar critérios customizados")
            raise HTTPException(
                status_code=500,
                detail="Erro interno do servidor"
            ) from e
