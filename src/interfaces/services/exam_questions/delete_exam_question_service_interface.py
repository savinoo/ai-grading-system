from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

class DeleteExamQuestionServiceInterface(ABC):
    """
    Interface para serviço de remoção de questão de prova.
    """

    @abstractmethod
    async def delete_exam_question(
        self,
        db: Session,
        question_uuid: UUID
    ) -> None:
        """
        Remove uma questão de uma prova.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
        """
        raise NotImplementedError()
