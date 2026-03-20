from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.responses.classes.class_with_students_response import ClassWithStudentsResponse

class GetClassWithStudentsServiceInterface(ABC):
    """
    Interface para o serviço de busca de turma com alunos.
    """
    
    @abstractmethod
    async def get_class_with_students(
        self,
        db: Session,
        class_uuid: UUID,
        *,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> ClassWithStudentsResponse:
        """
        Busca uma turma e seus alunos.
        
        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            active_only: Se deve retornar apenas alunos ativos
            skip: Número de alunos a pular na paginação
            limit: Número máximo de alunos a retornar
            
        Returns:
            ClassWithStudentsResponse: Turma com lista de alunos
        """
        raise NotImplementedError()
