from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

class DeleteAllQuestionAnswersServiceInterface(ABC):
    """
    Interface para serviço de remoção de todas as respostas de uma questão.
    """

    @abstractmethod
    async def delete_all_question_answers(
        self,
        db: Session,
        question_uuid: UUID
    ) -> int:
        """
        Remove todas as respostas de uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            
        Returns:
            int: Número de respostas removidas
        """
        raise NotImplementedError()
