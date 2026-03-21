from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session


class ValidateRecoveryCodeServiceInterface(ABC):
    """
    Interface para serviço de validação de código de recuperação.
    """
    
    @abstractmethod
    def validate(self, db:Session,  email: str, code: str) -> Dict[str, Any]:
        """
        Valida código de recuperação sem limpar.
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            code: Código de recuperação informado
            
        Returns:
            Dict com status da validação
            
        Raises:
            NotFoundError: Se usuário não for encontrado
            UnauthorizedError: Se código for inválido
        """
        raise NotImplementedError()
