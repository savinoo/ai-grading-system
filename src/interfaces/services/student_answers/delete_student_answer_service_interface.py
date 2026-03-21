from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

class DeleteStudentAnswerServiceInterface(ABC):
    """
    Interface para serviço de remoção de resposta de aluno.
    """

    @abstractmethod
    async def delete_student_answer(
        self,
        db: Session,
        answer_uuid: UUID
    ) -> None:
        """
        Remove uma resposta de aluno.
        
        Args:
            db: Sessão do banco de dados
            answer_uuid: UUID da resposta
        """
        raise NotImplementedError()
