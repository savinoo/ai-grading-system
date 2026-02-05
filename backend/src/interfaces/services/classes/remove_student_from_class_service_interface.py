from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.orm import Session

class RemoveStudentFromClassServiceInterface(ABC):
    """
    Interface para o serviço de remoção de aluno de uma turma.
    """
    
    @abstractmethod
    async def remove_student_from_class(
        self,
        db: Session,
        class_uuid: UUID,
        student_uuid: UUID
    ) -> dict:
        """
        Remove um aluno de uma turma.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            student_uuid: UUID do aluno
            
        Returns:
            dict: Informações sobre a remoção
        """
        raise NotImplementedError()
