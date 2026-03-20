from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.interfaces.services.users.resend_verification_email_service_interface import (
    ResendVerificationEmailServiceInterface
)
from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger
from src.core.brevo_handler import BrevoHandler


class ResendVerificationEmailService(ResendVerificationEmailServiceInterface):
    """
    Serviço responsável por reenviar o email de verificação.
    """
    
    def __init__(self, repository: UserRepositoryInterface) -> None:
        self.__repository = repository
        self.__logger = get_logger(__name__)
        self.__brevo_handler = BrevoHandler()
    
    async def resend_verification_email(self, db: Session, email: str) -> dict:
        """
        Reenvia email de verificação para um usuário.
        
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
            self.__logger.info("Reenviando email de verificação para: %s", email)
            
            # Busca usuário por email
            user = self.__repository.get_by_email(db, email)
            
            if not user:
                self.__logger.warning("Usuário não encontrado: %s", email)
                raise NotFoundError(
                    message="Usuário não encontrado",
                    context={"email": email}
                )
            
            # Verifica se o email já foi verificado
            if user.email_verified:
                self.__logger.info("Email já verificado para: %s", email)
                return {
                    "message": "Email já foi verificado anteriormente",
                    "email": user.email,
                    "already_verified": True
                }
            
            # Envia email de verificação via Brevo
            email_sent = await self.__brevo_handler.send_verification_email(
                email=user.email,
                user_uuid=user.uuid
            )
            
            if not email_sent:
                self.__logger.error("Falha ao enviar email de verificação para %s", email)
                raise SqlError(
                    message="Falha ao enviar email de verificação",
                    context={"email": email}
                )
            
            self.__logger.info("Email de verificação reenviado para: %s", email)
            
            return {
                "message": "Email de verificação enviado com sucesso",
                "email": user.email,
                "already_verified": False
            }
            
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.__logger.error("Erro ao buscar usuário: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao acessar banco de dados",
                context={"email": email},
                cause=e
            ) from e
        except Exception as e:
            self.__logger.error("Erro ao reenviar email: %s", e, exc_info=True)
            raise SqlError(
                message="Erro ao reenviar email de verificação",
                context={"email": email},
                cause=e
            ) from e
