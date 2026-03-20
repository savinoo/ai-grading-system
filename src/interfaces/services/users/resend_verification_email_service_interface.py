from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class ResendVerificationEmailServiceInterface(ABC):
    """
    Interface para serviço de reenvio de email de verificação.
    """
    
    @abstractmethod
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
        raise NotImplementedError
