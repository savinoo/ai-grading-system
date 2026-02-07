from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface

from src.interfaces.services.attachments.manage_attachments_service_interface import ManageAttachmentsServiceInterface

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger


class GetAttachmentsByExamController(ControllerInterface):
    """
    Controller responsável por listar anexos de uma prova.
    """

    def __init__(self, service: ManageAttachmentsServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de listagem de anexos de uma prova.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP com a lista de anexos
            
        Raises:
            HTTPException: Em caso de erro
        """
        db = http_request.db
        caller = http_request.caller
        token_infos = http_request.token_infos
        params = http_request.param or {}

        self.__logger.debug(
            "Handling get attachments by exam request from caller: %s",
            caller.caller_user if caller else "unknown"
        )

        try:
            # Valida autenticação
            if not token_infos or not token_infos.get("sub"):
                raise HTTPException(
                    status_code=401,
                    detail={"error": "Usuário não autenticado"}
                )

            # Pega parâmetros
            exam_uuid_str = params.get("exam_uuid")
            skip = params.get("skip", 0)
            limit = params.get("limit", 100)

            if not exam_uuid_str:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "exam_uuid é obrigatório"}
                )

            exam_uuid = UUID(exam_uuid_str)

            # Busca anexos
            attachments = asyncio.run(
                self.__service.get_by_exam_uuid(
                    db,
                    exam_uuid,
                    skip=skip,
                    limit=limit
                )
            )

            # Conta total
            total = asyncio.run(self.__service.count_by_exam_uuid(db, exam_uuid))

            self.__logger.info(
                "Listados %d anexos da prova %s",
                len(attachments),
                exam_uuid
            )

            return HttpResponse(
                status_code=200,
                body={
                    "attachments": [att.model_dump(mode='json') for att in attachments],
                    "total": total,
                    "skip": skip,
                    "limit": limit
                }
            )

        except ValueError as val_err:
            self.__logger.warning("UUID inválido: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID inválido"}
            ) from val_err

        except NotFoundError as not_found_err:
            self.__logger.warning("Prova não encontrada para listagem de anexos: %s", not_found_err)
            raise HTTPException(
                status_code=404,
                detail={"error": str(not_found_err)}
            ) from not_found_err

        except SqlError as sql_err:
            self.__logger.error(
                "Erro de banco de dados ao listar anexos: %s",
                sql_err,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro ao listar anexos",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error(
                "Erro inesperado ao listar anexos: %s",
                e,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro inesperado ao listar anexos"}
            ) from e
