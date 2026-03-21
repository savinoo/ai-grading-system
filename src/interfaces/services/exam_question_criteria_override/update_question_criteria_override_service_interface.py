from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.requests.exam_question_criteria_override.criteria_override_update_request import (
    ExamQuestionCriteriaOverrideUpdateRequest,
)
from src.domain.responses.exam_question_criteria_override.criteria_override_response import (
    ExamQuestionCriteriaOverrideResponse,
)

class UpdateQuestionCriteriaOverrideServiceInterface(ABC):
    """
    Interface para serviço de atualização de sobrescrita de critério de questão.
    """

    @abstractmethod
    async def update_question_criteria_override(
        self,
        db: Session,
        override_uuid: UUID,
        request: ExamQuestionCriteriaOverrideUpdateRequest
    ) -> ExamQuestionCriteriaOverrideResponse:
        """
        Atualiza uma sobrescrita de critério de questão.
        """
        raise NotImplementedError()
