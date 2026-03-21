from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.requests.exam_question_criteria_override.criteria_override_create_request import ExamQuestionCriteriaOverrideCreateRequest
from src.domain.responses.exam_question_criteria_override.criteria_override_response import ExamQuestionCriteriaOverrideResponse

class CreateQuestionCriteriaOverrideServiceInterface(ABC):
    """
    Interface para serviço de criação de sobrescrita de critério de questão.
    """

    @abstractmethod
    async def create_question_criteria_override(
        self,
        db: Session,
        request: ExamQuestionCriteriaOverrideCreateRequest
    ) -> ExamQuestionCriteriaOverrideResponse:
        """
        Cria uma sobrescrita de critério para uma questão.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da sobrescrita a ser criada
            
        Returns:
            ExamQuestionCriteriaOverrideResponse: Dados da sobrescrita criada
        """
        raise NotImplementedError()
