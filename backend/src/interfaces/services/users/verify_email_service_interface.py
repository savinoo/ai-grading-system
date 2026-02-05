from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.http.caller_domains import CallerMeta


class VerifyEmailServiceInterface(ABC):
    """
    Interface para serviço de verificação de email.
    """
    
    @abstractmethod
    def verify_email(self, db: Session, user_uuid: UUID, caller_meta: CallerMeta) -> dict:
        """
        Verifica o email de um usuário.
        
        Args:
            db: Sessão do banco de dados
            user_uuid: UUID do usuário
            caller_meta: Metadados do chamador (IP, etc)
            
        Returns:
            dict: Mensagem de sucesso
            
        Raises:
            NotFoundError: Se o usuário não for encontrado
            SqlError: Em caso de erro de banco de dados
        """
        raise NotImplementedError
