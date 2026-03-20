"""
Controller para publicação de provas.
Endpoint: POST /exams/{exam_uuid}/publish
"""

from __future__ import annotations

from uuid import UUID
from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.async_controllers_interface import AsyncControllerInterface
from src.interfaces.services.exams.publish_exam_service_interface import PublishExamServiceInterface

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.validate_error import ValidateError
from src.errors.domain.sql_error import SqlError
from src.core.logging_config import get_logger


class PublishExamController(AsyncControllerInterface):
    """
    Controller que delega ao PublishExamService a publicação de uma prova.
    """

    def __init__(self, service: PublishExamServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    async def handle(
        self,
        http_request: HttpRequest
    ) -> HttpResponse:
        """
        Processa a requisição de publicação de prova.
        
        Fluxo:
        1. Validar que prova existe e está em DRAFT
        2. Atualizar status para PUBLISHED
        3. Retornar HTTP 202 Accepted
        4. Background task faz indexação + correção
        
        Args:
            http_request: Requisição HTTP contendo exam_uuid no param e background_tasks em context
            
        Returns:
            HttpResponse: Resposta HTTP 202 com detalhes da publicação
            
        Raises:
            HTTPException: Em caso de erro
        """

        db = http_request.db
        caller = http_request.caller
        background_tasks = http_request.context.get('background_tasks')

        self.__logger.debug(
            "Handling publish exam request from caller: %s - %s - %s", 
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            exam_uuid_str = http_request.param.get("exam_uuid")
            
            if not exam_uuid_str:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "UUID da prova é obrigatório"}
                )
            
            # Converter string para UUID
            try:
                exam_uuid = UUID(exam_uuid_str)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "UUID da prova inválido"}
                ) from exc

            # Chamar service assincronamente
            result = await self.__service.publish_exam(
                db=db,
                exam_uuid=exam_uuid,
                background_tasks=background_tasks
            )

            self.__logger.info("Prova publicada com sucesso: %s", exam_uuid)

            return HttpResponse(
                status_code=202,
                body=result
            )

        except NotFoundError as not_found_err:
            self.__logger.warning("Prova não encontrada: %s", not_found_err.message)
            raise HTTPException(
                status_code=404,
                detail={
                    "error": not_found_err.message,
                    "context": not_found_err.context
                }
            ) from not_found_err

        except ValidateError as validation_err:
            self.__logger.warning("Erro de validação: %s", validation_err.message)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": validation_err.message,
                    "context": validation_err.context
                }
            ) from validation_err

        except SqlError as sql_err:
            self.__logger.error("Erro de banco de dados ao publicar prova: %s", sql_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao publicar prova",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error("Erro inesperado ao publicar prova: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno do servidor"}
            ) from e
