from uuid import UUID
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from src.domain.responses.reviews import ExamReviewResponse

class ExamReviewQueryServiceInterface(ABC):
    """Serviço para consulta de dados de revisão de provas."""
    
    @abstractmethod
    def get_exam_review(self, db: Session, exam_uuid: UUID, user_uuid: UUID) -> ExamReviewResponse:
        """Retorna dados completos para revisão de uma prova."""
        raise NotImplementedError()
