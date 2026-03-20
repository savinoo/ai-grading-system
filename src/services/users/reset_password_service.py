from datetime import datetime, timezone
from typing import Dict, Any
import asyncio

from sqlalchemy.orm import Session

from src.interfaces.services.users.reset_password_service_interface import ResetPasswordServiceInterface
from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface
from src.core.security.hash_password import HashPasswordHandler
from src.core.brevo_handler import BrevoHandler
from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError
from src.core.logging_config import get_logger


class ResetPasswordService(ResetPasswordServiceInterface):
    """
    Serviço para reset de senha usando código de recuperação.
    
    Valida o código, atualiza a senha e limpa o código de recuperação.
    """
    
    def __init__(self, user_repository: UserRepositoryInterface):
        self.__user_repository = user_repository
        self.__hash_handler = HashPasswordHandler()
        self.__brevo_handler = BrevoHandler()
        self.__logger = get_logger(__name__)
    
    def reset_password(self, db: Session, email: str, code: str, new_password: str) -> Dict[str, Any]:
        """
        Reseta senha do usuário usando código de recuperação.
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            code: Código de recuperação
            new_password: Nova senha (será hasheada)
            
        Returns:
            Dict com confirmação de reset
            
        Raises:
            NotFoundError: Se usuário não for encontrado
            UnauthorizedError: Se código for inválido
        """
        self.__logger.info("Resetando senha para: %s", email)
        
        # Busca usuário por email
        user = self.__user_repository.get_by_email(db, email)
        if not user:
            self.__logger.warning("Usuário não encontrado: %s", email)
            raise NotFoundError("Usuário não encontrado")
        
        # Verifica se existe código ativo
        if not user.recovery_code_hash:
            self.__logger.warning("Nenhum código de recuperação ativo para: %s", email)
            raise UnauthorizedError("Nenhum código de recuperação ativo")
        
        # Verifica se não expirou
        now = datetime.now(timezone.utc)
        if user.recovery_code_expires_at < now:
            self.__logger.warning("Código de recuperação expirado para: %s", email)
            raise UnauthorizedError("Código de recuperação expirado")
        
        # Verifica se não excedeu tentativas
        if user.recovery_code_attempts >= 3:
            self.__logger.warning("Número máximo de tentativas excedido para: %s", email)
            raise UnauthorizedError("Número máximo de tentativas excedido")
        
        # Verifica se código bate com hash
        is_valid = self.__hash_handler.verify_password(code, user.recovery_code_hash)
        
        if not is_valid:
            # Incrementa tentativas
            self.__user_repository.increment_recovery_code_attempts(db, user.id)
            self.__logger.warning(
                "Código de recuperação inválido para: %s (tentativa %d/3)",
                email, user.recovery_code_attempts + 1
            )
            raise UnauthorizedError("Código de recuperação inválido")
        
        # Código válido - hasheia e atualiza senha no banco
        new_password_hash = self.__hash_handler.generate_password_hash(new_password)
        self.__user_repository.update_password(db, user.id, new_password_hash)
        
        # Limpa código de recuperação no banco
        self.__user_repository.clear_recovery_code(db, user.id)
        
        # Limpa código de recuperação na Brevo
        asyncio.run(self.__brevo_handler.clear_recovery_code(email))
        
        self.__logger.info("Senha resetada com sucesso para: %s", email)
        
        return {
            "message": "Senha atualizada com sucesso",
            "email": email
        }
