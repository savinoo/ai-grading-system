from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DBAPIError, NoResultFound

from src.core.logging_config import get_logger

from src.domain.auth.auth import RevokeByJti

from src.interfaces.repositories.auth_refresh_token_repository_interface import AuthRefreshTokenRepositoryInterface
from src.interfaces.services.auth.revoke_by_jti_service_interface import RevokeByJtiServiceInterface

from src.models.entities.auth_refresh_token import AuthRefreshToken

from src.errors.domain.already_revoked import AlreadyRevokedError

class RevokeByJtiService(RevokeByJtiServiceInterface):
    """Revoga um token JWT com base no JTI fornecido.
    
    Attributes:
        __logger: Logger para registrar operações e erros.
        __repo: Repositório para operações de refresh tokens.
    """
    
    def __init__(self, repo: AuthRefreshTokenRepositoryInterface):
        self.__logger = get_logger(__name__)
        self.__repo = repo
        
    def revoke(self, db: Session, body: RevokeByJti) -> None:
        """
        Revoga um refresh token pelo JTI.
        
        Args:
            db: Sessão do banco de dados
            body: Dados contendo JTI e motivo da revogação
            
        Raises:
            NoResultFound: Se o token não for encontrado
            AlreadyRevokedError: Se o token já estiver revogado
            SQLAlchemyError: Se ocorrer erro no banco de dados
        """
        self.__logger.debug("Revogando token p/ jti=%s", body.jti)
        try:
            record: AuthRefreshToken = self.__repo.get_by_jti(db, body.jti)
            if not record:
                self.__logger.warning("Nenhum token encontrado para jti=%s", body.jti)
                raise NoResultFound(f"Nenhum token encontrado para jti={body.jti}")
        except NoResultFound as e:
            self.__logger.error("Erro ao buscar token para jti=%s: %s", body.jti, str(e), exc_info=True)
            raise e
        except (SQLAlchemyError, DBAPIError) as e:
            self.__logger.error("Erro ao buscar token para jti=%s: %s", body.jti, str(e), exc_info=True)
            raise e
        
        if record.is_revoked:
            self.__logger.info("Token jti=%s já está revogado", body.jti)
            raise AlreadyRevokedError(f"Token jti={body.jti} já está revogado")
        
        try:
            self.__logger.debug("Revogando token jti=%s", body.jti)
            self.__repo.revoke_by_jti(db=db, jti=body.jti)
        except (SQLAlchemyError, DBAPIError) as e:
            self.__logger.error("Erro ao revogar token jti=%s: %s", body.jti, str(e), exc_info=True)
            raise e
