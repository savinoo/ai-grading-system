from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session

from src.interfaces.services.users.validate_recovery_code_service_interface import ValidateRecoveryCodeServiceInterface
from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface

from src.core.security.hash_password import HashPasswordHandler
from src.core.logging_config import get_logger

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError


class ValidateRecoveryCodeService(ValidateRecoveryCodeServiceInterface):
    """
    Serviço para validação de código de recuperação.
    
    Verifica se o código é válido sem limpar (apenas incrementa tentativas se inválido).
    """
    
    def __init__(self, user_repository: UserRepositoryInterface):
        self.__user_repository = user_repository
        self.__hash_handler = HashPasswordHandler()
        self.__logger = get_logger(__name__)
    
    def validate(self, db:Session,  email: str, code: str) -> Dict[str, Any]:
        """
        Valida código de recuperação.
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            code: Código de recuperação informado
            
        Returns:
            Dict com status da validação
            
        Raises:
            NotFoundError: Se usuário não for encontrado
            UnauthorizedError: Se código for inválido, expirado ou tentativas excedidas
        """
        self.__logger.info("Validando código de recuperação para: %s", email)
        
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
        
        self.__logger.info("Código de recuperação válido para: %s", email)
        
        return {
            "message": "Código válido",
            "email": email
        }
