from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.async_controllers_interface import AsyncControllerInterface

from src.interfaces.services.attachments.manage_attachments_service_interface import ManageAttachmentsServiceInterface

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger


class DownloadAttachmentController(AsyncControllerInterface):
    """
    Controller responsável por buscar informações para download de anexo.
    """

    def __init__(self, service: ManageAttachmentsServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    async def handle(self, http_request: HttpRequest) -> HttpResponse:  # type: ignore[override]
        """
        Processa a requisição de download de anexo.
        
        Args:
            http_request: Requisição HTTP
            
        Returns:
            HttpResponse: Resposta HTTP com as informações do arquivo
            
        Raises:
            HTTPException: Em caso de erro
        """
        db = http_request.db
        caller = http_request.caller
        token_infos = http_request.token_infos
        params = http_request.param or {}

        self.__logger.debug(
            "Handling download attachment request from caller: %s",
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

            # Busca informações de download
            download_info = await self.__service.get_download_info(db, uuid)

            self.__logger.info(
                "Informações de download obtidas: %s",
                download_info["original_filename"]
            )

            return HttpResponse(
                status_code=200,
                body=download_info
            )

        except NotFoundError as not_found_err:
            self.__logger.warning("Anexo não encontrado: %s", not_found_err)
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
                "Erro de banco de dados ao buscar informações de download: %s",
                sql_err,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno do servidor"}
            ) from sql_err

        except HTTPException:
            raise

        except Exception as exc:
            self.__logger.error(
                "Erro inesperado ao buscar informações de download: %s",
                exc,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro interno do servidor"}
            ) from exc
