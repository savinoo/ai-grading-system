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


class DeleteAttachmentController(ControllerInterface):
    """
    Controller responsável por deletar um anexo.
    """

    def __init__(self, service: ManageAttachmentsServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição de deleção de anexo.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP confirmando a deleção
            
        Raises:
            HTTPException: Em caso de erro
        """
        db = http_request.db
        caller = http_request.caller
        token_infos = http_request.token_infos
        params = http_request.param or {}

        self.__logger.debug(
            "Handling delete attachment request from caller: %s",
            caller.caller_user if caller else "unknown"
        )

        try:
            # Valida autenticação
            if not token_infos or not token_infos.get("sub"):
                raise HTTPException(
                    status_code=401,
                    detail={"error": "Usuário não autenticado"}
                )

            # Pega UUID do anexo
            uuid_str = params.get("uuid")

            if not uuid_str:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "UUID é obrigatório"}
                )

            uuid = UUID(uuid_str)

            # Deleta anexo
            asyncio.run(self.__service.delete_by_uuid(db, uuid))

            self.__logger.info("Anexo deletado com sucesso: %s", uuid)

            return HttpResponse(
                status_code=200,
                body={
                    "message": "Anexo removido com sucesso",
                    "uuid": str(uuid)
                }
            )

        except NotFoundError as not_found_err:
            self.__logger.warning("Anexo não encontrado para deleção: %s", not_found_err)
            raise HTTPException(
                status_code=404,
                detail={"error": str(not_found_err)}
            ) from not_found_err

        except ValueError as val_err:
            self.__logger.warning("UUID inválido: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={"error": "UUID inválido"}
            ) from val_err

        except SqlError as sql_err:
            self.__logger.error(
                "Erro de banco de dados ao deletar anexo: %s",
                sql_err,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro ao deletar anexo",
                    "code": sql_err.code
                }
            ) from sql_err

        except Exception as e:
            self.__logger.error(
                "Erro inesperado ao deletar anexo: %s",
                e,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro inesperado ao deletar anexo"}
            ) from e
