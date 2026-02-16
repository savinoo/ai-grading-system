"""
Controller para aceitar sugestão da IA.
"""

from uuid import UUID
from typing import Any, Dict
from sqlalchemy.orm import Session

from src.interfaces.services.reviews.review_service_interface import ReviewServiceInterface
from src.domain.requests.reviews import AcceptSuggestionRequest
from src.core.logging_config import get_logger
from src.domain.http.caller_domains import CallerMeta


logger = get_logger(__name__)


class AcceptSuggestionController:
    """Controller para POST /reviews/suggestions/accept"""
    
    def __init__(self, review_service: ReviewServiceInterface):
        self.__review_service = review_service
    
    def handle(
        self,
        db: Session,
        request: AcceptSuggestionRequest,
        token_infos: Dict[str, Any],
        caller_meta: CallerMeta
    ) -> dict:
        """
        Aceita uma sugestão da IA.
        
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
            logger.error("Token inválido: UUID do usuário não encontrado")
            raise ValueError("Token inválido")
        
        logger.info(
            "Aceitando sugestão %s para resposta %s - Usuário: %s - IP: %s",
            request.suggestion_id,
            request.answer_uuid,
            user_uuid,
            caller_meta.ip
        )
        
        response = self.__review_service.accept_suggestion(
            db=db,
            request=request,
            user_uuid=UUID(user_uuid)
        )
        
        logger.info("Sugestão aceita com sucesso")
        
        return response
