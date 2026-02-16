"""
Interface para serviço de resultados de correção.
"""

from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.responses.results import ExamResultsResponse, GradingDetailsResponse


class ResultsServiceInterface(ABC):
    """Interface para serviço de resultados de provas corrigidas."""
    
    @abstractmethod
    def get_exam_results(self, db: Session, exam_uuid: UUID) -> ExamResultsResponse:
        """
        Retorna estatísticas e resultados de uma prova corrigida.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            
        Returns:
            ExamResultsResponse com estatísticas completas
            
        Raises:
            NotFoundError: Se a prova não existir
        """
        pass
    
    @abstractmethod
    def get_grading_details(
        self,
        db: Session,
        answer_uuid: UUID
    ) -> GradingDetailsResponse:
        """
        Retorna detalhes completos da correção de uma resposta.
        
        Args:
            db: Sessão do banco de dados
            answer_uuid: UUID da resposta do aluno
            
        Returns:
            GradingDetailsResponse com todos os detalhes da correção
            
        Raises:
            NotFoundError: Se a resposta não existir
        """
        pass
