from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

from src.core.logging_config import get_logger

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.auth.refresh_token_service_interface import RefreshTokenServiceInterface

from src.errors.domain.unauthorized import UnauthorizedError
from src.errors.domain.not_found import NotFoundError

class RefreshTokenController(ControllerInterface):
    """Controller para renovação de token JWT usando refresh token."""
    
    def __init__(self, service: RefreshTokenServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
        
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        self.__logger.debug("Iniciando refresh de token")
        
        db = http_request.db
        token_claims = http_request.token_infos
        
        if not token_claims:
            self.__logger.error("Token claims não encontrado no HttpRequest")
            raise HTTPException(status_code=401, detail="Token inválido.")
        
        try:
            body_response = self.__service.refresh(db, token_claims)
            return HttpResponse(200, body_response)
        
        except UnauthorizedError as ue:
            self.__logger.warning("Token não autorizado: %s", str(ue))
            raise HTTPException(status_code=401, detail=str(ue)) from ue
        
        except NotFoundError as nfe:
            self.__logger.error("Refresh token não encontrado: %s", str(nfe))
            raise HTTPException(status_code=404, detail=str(nfe)) from nfe
        
        except (SQLAlchemyError, DBAPIError) as db_err:
            self.__logger.error("Erro de banco de dados: %s", str(db_err), exc_info=True)
            raise HTTPException(status_code=500, detail="Erro de banco de dados.") from db_err
        
        except Exception as e:  # pylint: disable=broad-except
            self.__logger.error("Erro ao processar a requisição: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail="Erro interno do servidor.") from e
