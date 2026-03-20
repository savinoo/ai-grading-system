from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.requests.reviews import FinalizeReviewRequest

class ReviewFinalizationServiceInterface(ABC):
    """Serviço para finalização de revisão."""
    
    @abstractmethod    
    def finalize_review(
        self,
        db: Session,
        request: FinalizeReviewRequest,
        user_uuid: UUID
    ) -> dict:
        """
        Finaliza revisão e gera relatório.
        
        Ações realizadas:
        - Atualiza status da prova para FINALIZED
        - Atualiza status de todas as respostas para FINALIZED  
        - Marca graded_by em todas as respostas
        - Gera arquivo Excel com as notas
        """
        raise NotImplementedError()
