from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.interfaces.services.users.generate_recovery_code_service_interface import (
    GenerateRecoveryCodeServiceInterface
)
from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger
from src.core.brevo_handler import BrevoHandler
from src.core.security.hash_password import HashPasswordHandler
from src.core.settings import settings


class GenerateRecoveryCodeService(GenerateRecoveryCodeServiceInterface):
    """
    Serviço responsável por gerar código de recuperação e enviar por email.
    """
    
    def __init__(self, repository: UserRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)
        self.__brevo_handler = BrevoHandler()
        self.__hash_handler = HashPasswordHandler()
    
    async def generate_recovery_code(self, db: Session, email: str) -> dict:
        """
        Gera um código de recuperação e envia por email.
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            
        Returns:
            dict: Mensagem de confirmação
            
        Raises:
            NotFoundError: Se o usuário não for encontrado
            SqlError: Em caso de erro de banco de dados
        """
        try:
            self.__logger.info("Gerando código de recuperação para: %s", email)
            
            # Busca usuário por email
            user = self.__repository.get_by_email(db, email)
            
            if not user:
                self.__logger.warning("Usuário não encontrado: %s", email)
                raise NotFoundError(
                    message="Usuário não encontrado",
                    context={"email": email}
                )
            
            # Gera código numérico aleatório
            code_length = settings.RECOVERY_CODE_LENGTH
            recovery_code = ''.join([str(secrets.randbelow(10)) for _ in range(code_length)])
            
            # Gera hash do código
            code_hash = self.__hash_handler.generate_password_hash(recovery_code)
            
            # Calcula tempo de expiração
            expires_at = datetime.now() + timedelta(minutes=settings.RECOVERY_CODE_EXPIRY_MINUTES)
            
            # Salva código no banco
            self.__repository.set_recovery_code(db, user.id, code_hash, expires_at)
            
            # Envia código por email via Brevo
            email_sent = await self.__brevo_handler.send_recovery_code_email(
                email=user.email,
                recovery_code=recovery_code
            )
            
            if not email_sent:
                self.__logger.error("Falha ao enviar código de recuperação para %s", email)
                raise SqlError(
                    message="Falha ao enviar código de recuperação",
                    context={"email": email}
                )
            
            self.__logger.info(
                "Código de recuperação gerado e enviado para: %s (expira em %d min)",
                email,
                settings.RECOVERY_CODE_EXPIRY_MINUTES
            )
            
            return {
                "message": "Código de recuperação enviado com sucesso",
                "email": user.email,
                "expires_in_minutes": settings.RECOVERY_CODE_EXPIRY_MINUTES
            }
            
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao gerar código: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao acessar banco de dados",
                context={"email": email},
                cause=e
            ) from e
        except Exception as e:
            self.__logger.error("Erro ao gerar código de recuperação: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao gerar código de recuperação",
                context={"email": email},
                cause=e
            ) from e
