from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError, DBAPIError, NoResultFound

from src.core.logging_config import get_logger

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.auth.revoke_by_jti_service_interface import RevokeByJtiServiceInterface

from src.errors.domain.already_revoked import AlreadyRevokedError

class RevokeByJtiController (ControllerInterface):
    """Controller para revogação de token JWT por JTI."""
    
    def __init__(self, service: RevokeByJtiServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)
        
    def handle (self, http_request: HttpRequest) -> HttpResponse:
        self.__logger.debug("Chamando servico")
        
        db = http_request.db
        
        self.__logger.debug("meta: %s", http_request.caller)
        payload = http_request.body
        
        try:
            self.__service.revoke(body=payload, db=db)
            return HttpResponse(204)
        
        except NoResultFound as nfe:
            self.__logger.error("Token não encontrado: %s", str(nfe), exc_info=True)
            raise HTTPException(status_code=404, detail="Token não encontrado.") from nfe
        
        except (SQLAlchemyError, DBAPIError) as dbe:
            self.__logger.error("Erro de banco de dados: %s", str(dbe), exc_info=True)
            raise HTTPException(status_code=500, detail="Erro de banco de dados.") from dbe
        
        except AlreadyRevokedError as are:
            self.__logger.info("Token já revogado: %s", str(are))
            raise HTTPException(status_code=400, detail="Token já revogado.") from are
        
        except Exception as e: # pylint: disable=broad-except
            self.__logger.error("Erro ao processar a requisição: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail="Erro interno do servidor.") from e
