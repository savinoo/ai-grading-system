from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

class DeleteQuestionCriteriaOverrideServiceInterface(ABC):
    """
    Interface para serviço de remoção de sobrescrita de critério de questão.
    """

    @abstractmethod
    async def delete_question_criteria_override(
        self,
        db: Session,
        override_uuid: UUID
    ) -> None:
        """
        Remove uma sobrescrita de critério de questão.
        """
        raise NotImplementedError()
