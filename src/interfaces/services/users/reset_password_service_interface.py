from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session


class ResetPasswordServiceInterface(ABC):
    """
    Interface para serviço de reset de senha com código de recuperação.
    """
    
    @abstractmethod
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
        raise NotImplementedError()
