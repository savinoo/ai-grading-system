from uuid import UUID
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from src.domain.requests.reviews import AdjustGradeRequest

class GradeAdjustmentServiceInterface(ABC):
    """Serviço para ajuste de notas."""
    
    @abstractmethod
    def adjust_grade(
        self,
        db: Session,
        request: AdjustGradeRequest,
        user_uuid: UUID
    ) -> dict:
        """Ajusta nota manualmente."""
        raise NotImplementedError()
