from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class GenerateRecoveryCodeServiceInterface(ABC):
    """
    Interface para serviço de geração de código de recuperação.
    """
    
    @abstractmethod
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
        raise NotImplementedError
