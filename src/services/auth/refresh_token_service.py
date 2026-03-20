from __future__ import annotations

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

from src.core.logging_config import get_logger
from src.core.security.jwt import JWTHandler
from src.core.settings import settings

from src.interfaces.repositories.auth_refresh_token_repository_interface import AuthRefreshTokenRepositoryInterface
from src.interfaces.services.auth.refresh_token_service_interface import RefreshTokenServiceInterface

from src.errors.domain.unauthorized import UnauthorizedError
from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError


class RefreshTokenService(RefreshTokenServiceInterface):
    """
    Serviço responsável por renovar tokens de acesso usando refresh tokens.
    """
    
    def __init__(
        self, 
        refresh_token_repo: AuthRefreshTokenRepositoryInterface
    ):
        self.__logger = get_logger(__name__)
        self.__refresh_token_repo = refresh_token_repo
        self.__jwt_handler = JWTHandler()
    
    def refresh(self, db: Session, token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """
        Renova um token de acesso usando um refresh token válido.
        
        Args:
            db (Session): Sessão do banco de dados.
            token_claims (Dict[str, Any]): Claims do refresh token já decodificado.
            
        Returns:
            Dict[str, Any]: Novo token de acesso.
            
        Raises:
            UnauthorizedError: Se o refresh token for inválido ou revogado.
            NotFoundError: Se o refresh token não for encontrado no banco de dados.
            SqlError: Se ocorrer um erro ao acessar o banco de dados.
            Exception: Para outros erros inesperados.
        """
        self.__logger.debug("Iniciando processo de refresh de token")
        
        token_type = token_claims.get("typ")
        if token_type != "REFRESH":
            self.__logger.warning("Token fornecido não é do tipo REFRESH: %s", token_type)
            raise UnauthorizedError("Token fornecido não é um refresh token.")
        
        jti = token_claims.get("jti")
        if not jti:
            self.__logger.error("JTI não encontrado no payload do token")
            raise UnauthorizedError("Token inválido.")
        
        try:
            token_record = self.__refresh_token_repo.get_active_by_jti(db, jti)
            if not token_record:
                self.__logger.warning("Refresh token com JTI %s não encontrado ou inativo", jti)
                raise NotFoundError("Refresh token não encontrado ou inválido.")
        except (SQLAlchemyError, DBAPIError) as e:
            self.__logger.error("Erro ao buscar refresh token no banco de dados: %s", str(e))
            raise SqlError("Erro ao acessar o banco de dados.") from e
        
        # Verifica se token está válido
        if not token_record.is_valid:
            self.__logger.warning("Refresh token %s não é válido", jti)
            raise UnauthorizedError("Refresh token inválido ou expirado.")
        
        sub = str(token_record.subject)
        
        # Parseia scopes
        scopes = token_record.scopes if token_record.scopes else []
        
        self.__logger.debug("Criando novo token ACCESS para sub=%s com scopes=%s", sub, scopes)
        
        try:
            access_token = self.__jwt_handler.create_access_token(subject=sub, scopes=scopes)
        except Exception as e:
            self.__logger.error("Erro ao criar novo token ACCESS: %s", str(e))
            raise e
        
        self.__logger.debug("Token ACCESS criado com sucesso")
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_TTL
        }
