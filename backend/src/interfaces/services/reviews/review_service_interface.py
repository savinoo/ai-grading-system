"""
Interface do serviço de revisão de provas.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.responses.reviews import ExamReviewResponse
from src.domain.requests.reviews import (
    AcceptSuggestionRequest,
    RejectSuggestionRequest,
    AdjustGradeRequest,
    FinalizeReviewRequest
)


class ReviewServiceInterface(ABC):
    """Interface para o serviço de revisão de provas."""
    
    @abstractmethod
    def get_exam_review(self, db: Session, exam_uuid: UUID, user_uuid: UUID) -> ExamReviewResponse:
        """
        Retorna dados completos para revisão de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            user_uuid: UUID do professor (para validação)
            
        Returns:
            ExamReviewResponse com questões e respostas dos alunos
            
        Raises:
            NotFoundError: Se prova não for encontrada
            UnauthorizedError: Se usuário não for dono da prova
        """
        pass
    
    @abstractmethod
    def accept_suggestion(
        self,
        db: Session,
        request: AcceptSuggestionRequest,
        user_uuid: UUID
    ) -> dict:
        """
        Aceita uma sugestão da IA.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da solicitação
            user_uuid: UUID do professor
            
        Returns:
            Dict com mensagem de sucesso
        """
        pass
    
    @abstractmethod
    def reject_suggestion(
        self,
        db: Session,
        request: RejectSuggestionRequest,
        user_uuid: UUID
    ) -> dict:
        """
        Rejeita uma sugestão da IA.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da solicitação
            user_uuid: UUID do professor
            
        Returns:
            Dict com mensagem de sucesso
        """
        pass
    
    @abstractmethod
    def adjust_grade(
        self,
        db: Session,
        request: AdjustGradeRequest,
        user_uuid: UUID
    ) -> dict:
        """
        Ajusta nota manualmente.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da solicitação
            user_uuid: UUID do professor
            
        Returns:
            Dict com mensagem de sucesso e nova nota
        """
        pass
    
    @abstractmethod
    def finalize_review(
        self,
        db: Session,
        request: FinalizeReviewRequest,
        user_uuid: UUID
    ) -> dict:
        """
        Finaliza revisão e gera relatório.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da solicitação
            user_uuid: UUID do professor
            
        Returns:
            Dict com mensagem de sucesso e link do relatório (quando aplicável)
        """
        pass
