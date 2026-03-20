from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.interfaces.services.users.verify_email_service_interface import VerifyEmailServiceInterface
from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface
from src.interfaces.repositories.auth_refresh_token_repository_interface import (
    AuthRefreshTokenRepositoryInterface
)

from src.domain.http.caller_domains import CallerMeta

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger
from src.core.security.jwt import JWTHandler
from src.core.settings import settings


class VerifyEmailService(VerifyEmailServiceInterface):
    """
    Serviço responsável por verificar o email de um usuário e realizar login automático.
    """
    
    def __init__(
        self,
        repository: UserRepositoryInterface,
        refresh_token_repository: AuthRefreshTokenRepositoryInterface
    ) -> None:
        self.__repository = repository
        self.__refresh_token_repository = refresh_token_repository
        self.__logger = get_logger(__name__)
        self.__jwt_handler = JWTHandler()
    
    def verify_email(self, db: Session, user_uuid: UUID, caller_meta: CallerMeta) -> dict:
        """
        Verifica o email de um usuário e realiza login automático.
        
        Args:
            db: Sessão do banco de dados
            user_uuid: UUID do usuário
            caller_meta: Metadados do chamador (IP, etc)
            
        Returns:
            dict: Tokens de autenticação e dados do usuário
            
        Raises:
            NotFoundError: Se o usuário não for encontrado
            SqlError: Em caso de erro de banco de dados
        """
        try:
            self.__logger.info("Verificando email do usuário: %s", user_uuid)
            
            # Busca usuário por UUID
            user = self.__repository.get_by_uuid(db, user_uuid)
            
            # Verifica se o email já foi verificado
            already_verified = user.email_verified
            
            if not already_verified:
                # Marca email como verificado
                self.__repository.verify_email(db, user.id)
                self.__logger.info("Email verificado com sucesso: %s", user.email)
            else:
                self.__logger.info("Email já verificado para usuário: %s", user_uuid)
            
            # Gera tokens JWT para login automático
            user_uuid_str = str(user.uuid)
            scopes = [user.user_type]

            access_token = self.__jwt_handler.create_access_token(
                subject=user_uuid_str, scopes=scopes
            )

            refresh_token_jwt = self.__jwt_handler.create_refresh_token(
                subject=user_uuid_str, scopes=scopes
            )

            # Decodifica refresh token para pegar JTI
            refresh_payload = self.__jwt_handler.decode_jwt_token(refresh_token_jwt)

            # Persiste refresh token no banco
            self.__refresh_token_repository.create(
                db=db,
                jti=refresh_payload["jti"],
                subject=user.uuid,
                issued_at=datetime.fromtimestamp(refresh_payload["iat"]),
                not_before=datetime.fromtimestamp(refresh_payload["iat"]),
                expires_at=datetime.fromtimestamp(refresh_payload["exp"]),
                scopes=scopes,
                issued_ip=caller_meta.ip,
                token_version=1,
            )

            # Atualiza last_login_at do usuário
            user.last_login_at = datetime.now()
            db.flush()
            
            return {
                "message": "Email verificado com sucesso" if not already_verified else "Email já verificado, login realizado",
                "already_verified": already_verified,
                "access_token": access_token,
                "refresh_token": refresh_token_jwt,
                "token_type": "Bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_TTL,
                "user_uuid": str(user.uuid),
                "email": user.email,
                "user_type": user.user_type,
            }
            
        except NoResultFound as e:
            self.__logger.warning("Usuário não encontrado: %s", user_uuid)
            raise NotFoundError(
                message="Usuário não encontrado",
                context={"uuid": str(user_uuid)},
                cause=e
            ) from e
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao verificar email: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao verificar email no banco de dados",
                context={"uuid": str(user_uuid)},
                cause=e
            ) from e
