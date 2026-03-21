from uuid import UUID
from typing import Any, Dict
from sqlalchemy.orm import Session

from src.interfaces.services.reviews.review_finalization_service_interface import ReviewFinalizationServiceInterface
from src.domain.requests.reviews import FinalizeReviewRequest
from src.core.logging_config import get_logger
from src.domain.http.caller_domains import CallerMeta


class FinalizeReviewController:
    """Controller para POST /reviews/finalize"""
    
    def __init__(self, finalization_service: ReviewFinalizationServiceInterface):
        self.__finalization_service = finalization_service
        self.__logger = get_logger("controllers")
    
    def handle(
        self,
        db: Session,
        request: FinalizeReviewRequest,
        token_infos: Dict[str, Any],
        caller_meta: CallerMeta
    ) -> dict:
        """
        Finaliza revisão e gera relatório.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da solicitação
            token_infos: Informações do token JWT
            caller_meta: Metadados da chamada
            
        Returns:
            Dict com mensagem de sucesso
        """
        
        user_uuid = token_infos.get("sub")
        if not user_uuid:
            self.__logger.error("Token inválido: UUID do usuário não encontrado")
            raise ValueError("Token inválido")
        
        self.__logger.info(
            "Finalizando revisão da prova %s - Usuário: %s - IP: %s - PDF: %s - Notificações: %s",
            request.exam_uuid,
            user_uuid,
            caller_meta.ip,
            request.generate_pdf,
            request.send_notifications
        )
        
        response = self.__finalization_service.finalize_review(
            db=db,
            request=request,
            user_uuid=UUID(user_uuid)
        )
        
        self.__logger.info("Revisão finalizada com sucesso")
        
        return response
