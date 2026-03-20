from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

class DeleteExamCriteriaServiceInterface(ABC):
    """
    Interface para serviço de remoção de critério de prova.
    """

    @abstractmethod
    async def delete_exam_criteria(
        self,
        db: Session,
        exam_criteria_uuid: UUID
    ) -> None:
        """
        Remove um critério de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_uuid: UUID do critério de prova
        """
        raise NotImplementedError()
