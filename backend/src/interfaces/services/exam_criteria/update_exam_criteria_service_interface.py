from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.requests.exam_criteria.exam_criteria_update_request import ExamCriteriaUpdateRequest
from src.domain.responses.exam_criteria.exam_criteria_response import ExamCriteriaResponse

class UpdateExamCriteriaServiceInterface(ABC):
    """
    Interface para serviço de atualização de critério de prova.
    """

    @abstractmethod
    async def update_exam_criteria(
        self,
        db: Session,
        exam_criteria_uuid: UUID,
        request: ExamCriteriaUpdateRequest
    ) -> ExamCriteriaResponse:
        """
        Atualiza um critério de prova (peso e/ou pontuação máxima).
        
        Args:
            db: Sessão do banco de dados
            exam_criteria_uuid: UUID do critério de prova
            request: Dados a serem atualizados
            
        Returns:
            ExamCriteriaResponse: Dados do critério atualizado
        """
        raise NotImplementedError()
