from __future__ import annotations

from typing import BinaryIO

from fastapi import HTTPException

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.async_controllers_interface import AsyncControllerInterface

from src.interfaces.services.attachments.upload_attachment_service_interface import UploadAttachmentServiceInterface

from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger


class UploadAttachmentController(AsyncControllerInterface):
    """
    Controller responsável por processar requisições de upload de anexos.
    """

    def __init__(self, service: UploadAttachmentServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    async def handle(self, http_request: HttpRequest) -> HttpResponse:  # type: ignore[override]
        """
        Processa a requisição de upload de anexo.
        
        Args:
            http_request: Requisição HTTP contendo o arquivo e metadados
            
        Returns:
            HttpResponse: Resposta HTTP com os dados do anexo criado
            
        Raises:
            HTTPException: Em caso de erro
        """
        db = http_request.db
        caller = http_request.caller
        token_infos = http_request.token_infos

        self.__logger.debug(
            "Handling upload attachment request from caller: %s - %s - %s",
            caller.caller_app if caller else "unknown",
            caller.caller_user if caller else "unknown",
            caller.ip if caller else "unknown"
        )

        try:
            # Valida autenticação
            if not token_infos or not token_infos.get("sub"):
                raise HTTPException(
                    status_code=401,
                    detail={"error": "Usuário não autenticado"}
                )

            # O body deve conter o AttachmentUploadRequest
            request = http_request.body.get("request")
            file: BinaryIO = http_request.body.get("file")

            if not request or not file:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "Request ou arquivo ausente"}
                )

            # Faz o upload
            result = await self.__service.upload(db, file, request)

            self.__logger.info(
                "Anexo enviado com sucesso: %s (prova: %s)",
                result.uuid,
                result.exam_uuid
            )

            return HttpResponse(
                status_code=201,
                body=result
            )

        except SqlError as sql_err:
            self.__logger.error(
                "Erro de banco de dados ao fazer upload de anexo: %s",
                sql_err,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Erro de banco de dados ao fazer upload do anexo",
                    "code": sql_err.code
                }
            ) from sql_err

        except ValueError as val_err:
            self.__logger.warning("Erro de validação no upload: %s", val_err)
            raise HTTPException(
                status_code=400,
                detail={"error": str(val_err)}
            ) from val_err

        except Exception as e:
            self.__logger.error(
                "Erro inesperado ao fazer upload de anexo: %s",
                e,
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "Erro inesperado ao fazer upload do anexo"}
            ) from e
