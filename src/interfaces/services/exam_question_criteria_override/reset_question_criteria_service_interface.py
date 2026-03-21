from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

class ResetQuestionCriteriaServiceInterface(ABC):
    """
    Interface para serviço de reset de critérios de questão.
    """

    @abstractmethod
    async def reset_question_criteria(
        self,
        db: Session,
        question_uuid: UUID
    ) -> int:
        """
        Remove todas as sobrescritas de critérios de uma questão,
        resetando para os critérios originais da prova.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            
        Returns:
            int: Número de sobrescritas removidas
        """
        raise NotImplementedError()
