from uuid import UUID
from typing import Any, Dict
from sqlalchemy.orm import Session

from src.interfaces.services.reviews.grade_adjustment_service_interface import GradeAdjustmentServiceInterface
from src.domain.requests.reviews import AdjustGradeRequest
from src.core.logging_config import get_logger
from src.domain.http.caller_domains import CallerMeta


logger = get_logger(__name__)


class AdjustGradeController:
    """Controller para PUT /reviews/grades/adjust"""
    
    def __init__(self, adjustment_service: GradeAdjustmentServiceInterface):
        self.__adjustment_service = adjustment_service
    
    def handle(
        self,
        db: Session,
        request: AdjustGradeRequest,
        token_infos: Dict[str, Any],
        caller_meta: CallerMeta
    ) -> dict:
        """
        Ajusta nota manualmente.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da solicitação
            token_infos: Informações do token JWT
            caller_meta: Metadados da chamada
            
        Returns:
            Dict com mensagem de sucesso e nova nota
        """
        
        user_uuid = token_infos.get("sub")
        if not user_uuid:
            logger.error("Token inválido: UUID do usuário não encontrado")
            raise ValueError("Token inválido")
        
        logger.info(
            "Ajustando nota da resposta %s para %.2f - Usuário: %s - IP: %s",
            request.answer_uuid,
            request.new_score,
            user_uuid,
            caller_meta.ip
        )
        
        response = self.__adjustment_service.adjust_grade(
            db=db,
            request=request,
            user_uuid=UUID(user_uuid)
        )
        
        logger.info("Nota ajustada com sucesso")
        
        return response
