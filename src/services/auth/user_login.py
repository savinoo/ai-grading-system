from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface
from src.interfaces.repositories.auth_refresh_token_repository_interface import (
    AuthRefreshTokenRepositoryInterface
)
from src.interfaces.services.auth.user_login_interface import UserLoginServiceInterface

from src.models.entities.user import User

from src.domain.requests.auth.login import UserLoginRequest
from src.domain.responses.auth.login import UserLoginResponse
from src.domain.http.caller_domains import CallerMeta

from src.core.logging_config import get_logger
from src.core.security.hash_password import HashPasswordHandler
from src.core.security.jwt import JWTHandler
from src.core.settings import settings

from src.errors.domain.unauthorized import UnauthorizedError
from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

class UserLoginService(UserLoginServiceInterface):
    """
    Serviço para autenticação de usuários e emissão de tokens JWT.
    """

    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        refresh_token_repository: AuthRefreshTokenRepositoryInterface,
    ):
        self.__user_repository = user_repository
        self.__refresh_token_repository = refresh_token_repository
        self.__logger = get_logger(__name__)
        self.__hash_password_handler = HashPasswordHandler()
        self.__jwt_handler = JWTHandler()

    def login(self, db: Session, user_request: UserLoginRequest, caller_meta: CallerMeta) -> UserLoginResponse:
        """
        Autentica um usuário usando email e senha, e retorna tokens JWT.

        Args:
            db: Sessão do banco de dados
            user_request: Objeto de requisição contendo email e senha
            caller_meta: Metadados do chamador (IP, app, user)

        Returns:
            UserLoginResponse: Resposta contendo tokens e dados do usuário

        Raises:
            NotFoundError: Se o usuário não for encontrado
            UnauthorizedError: Se a senha estiver incorreta ou usuário inativo
            SqlError: Se ocorrer um erro ao acessar o banco de dados
        """
        email = user_request.email
        password = user_request.password

        self.__logger.debug("Tentando autenticar usuário: %s", email)

        try:
            # Busca usuário por email
            user: User | None = self.__user_repository.get_active_by_email(db, email)

            if not user:
                self.__logger.warning("Usuário não encontrado ou inativo: %s", email)
                raise NotFoundError(f"Usuário com email '{email}' não encontrado ou inativo.")

            # Verifica senha
            if not self.__hash_password_handler.verify_password(password, user.password_hash):
                self.__logger.warning("Senha incorreta para usuário: %s", email)
                raise UnauthorizedError("Email ou senha incorretos.")

            # Verifica se usuário está ativo
            if not user.active or user.deleted_at is not None:
                self.__logger.warning("Tentativa de login para usuário inativo: %s", email)
                raise UnauthorizedError("Usuário inativo ou deletado.")

            # Gerencia limite de sessões ativas (máximo 4)
            active_token_count = self.__refresh_token_repository.count_active_by_subject(db, user.uuid)
            
            if active_token_count >= settings.MAX_ACTIVE_SESSIONS:
                # Busca os tokens ativos ordenados por data de criação (mais antigos primeiro)
                active_tokens = self.__refresh_token_repository.get_all_by_subject(
                    db, user.uuid, only_active=True
                )
                
                # Calcula quantos tokens precisam ser revogados
                tokens_to_revoke = active_token_count - settings.MAX_ACTIVE_SESSIONS + 1
                
                # Revoga os tokens mais antigos
                for token in active_tokens[-tokens_to_revoke:]:
                    self.__logger.debug(
                        "Revogando token antigo (limite de sessões): JTI=%s", 
                        token.jti
                    )
                    self.__refresh_token_repository.revoke_by_jti(db, token.jti)
                
                self.__logger.info(
                    "Revogados %d tokens antigos do usuário %s (limite de %d sessões)",
                    tokens_to_revoke, user.uuid, settings.MAX_ACTIVE_SESSIONS
                )

            # Cria tokens
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
            now = datetime.now()

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
            user.last_login_at = now
            db.flush()

            self.__logger.info("Login bem-sucedido para usuário: %s", email)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token_jwt,
                "token_type": "Bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_TTL,
                "user_uuid": str(user.uuid),
                "email": user.email,
                "user_type": user.user_type,
            }

        except NotFoundError:
            raise
        except UnauthorizedError:
            raise
        except (SQLAlchemyError, NoResultFound) as e:
            self.__logger.error(
                "Erro ao acessar o banco de dados ao autenticar usuário: %s. Erro: %s",
                email,
                str(e),
                exc_info=True,
            )
            raise SqlError("Erro ao acessar o banco de dados.") from e
        except Exception as e:
            self.__logger.error(
                "Erro inesperado ao autenticar usuário: %s. Erro: %s",
                email,
                str(e),
                exc_info=True,
            )
            raise SqlError("Erro inesperado ao autenticar usuário.") from e
