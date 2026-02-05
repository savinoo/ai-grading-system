from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.requests.classes.add_students_to_class_request import AddStudentsToClassRequest

class AddStudentsToClassServiceInterface(ABC):
    """
    Interface para o serviço de adição de alunos a turmas.
    """
    
    @abstractmethod
    async def add_students_to_class(
        self,
        db: Session,
        class_uuid: UUID,
        request: AddStudentsToClassRequest
    ) -> dict:
        """
        Adiciona alunos a uma turma.
        Cria novos alunos se não existirem (validando por nome e email).
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            request: Lista de alunos a adicionar
            
        Returns:
            dict: Informações sobre os alunos adicionados
        """
        raise NotImplementedError()
