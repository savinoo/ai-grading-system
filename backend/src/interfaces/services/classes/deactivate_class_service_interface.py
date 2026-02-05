from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.responses.classes.class_create_response import ClassCreateResponse

class DeactivateClassServiceInterface(ABC):
    """
    Interface para o serviço de desativação de turma.
    """
    
    @abstractmethod
    async def deactivate_class(
        self,
        db: Session,
        class_uuid: UUID
    ) -> ClassCreateResponse:
        """
        Desativa uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            
        Returns:
            ClassCreateResponse: Dados da turma desativada
        """
        raise NotImplementedError()
