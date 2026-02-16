"""
Controller para buscar dados de revisão de uma prova.
"""

from uuid import UUID
from typing import Any, Dict
from sqlalchemy.orm import Session

from src.interfaces.services.reviews.review_service_interface import ReviewServiceInterface
from src.domain.responses.reviews import ExamReviewResponse
from src.core.logging_config import get_logger
from src.domain.http.caller_domains import CallerMeta


logger = get_logger(__name__)


class GetExamReviewController:
    """Controller para GET /exams/{exam_uuid}/review"""
    
    def __init__(self, review_service: ReviewServiceInterface):
        self.__review_service = review_service
    
    def handle(
        self,
        db: Session,
        exam_uuid: UUID,
        token_infos: Dict[str, Any],
        caller_meta: CallerMeta
    ) -> ExamReviewResponse:
        """
        Busca dados de revisão de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            token_infos: Informações do token JWT
            caller_meta: Metadados da chamada
            
        Returns:
            ExamReviewResponse com dados de revisão
        """
        
        user_uuid = token_infos.get("sub")
        if not user_uuid:
            logger.error("Token inválido: UUID do usuário não encontrado")
            raise ValueError("Token inválido")
        
        logger.info(
            "Buscando dados de revisão da prova %s para usuário %s - IP: %s",
            exam_uuid,
            user_uuid,
            caller_meta.ip
        )
        
        response = self.__review_service.get_exam_review(
            db=db,
            exam_uuid=exam_uuid,
            user_uuid=UUID(user_uuid)
        )
        
        logger.info(
            "Dados de revisão retornados com sucesso: %d questões, %d alunos",
            response.total_questions,
            response.total_students
        )
        
        return response
