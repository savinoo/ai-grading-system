from uuid import UUID
from typing import Any, Dict
from sqlalchemy.orm import Session

from src.interfaces.services.reviews.answer_approval_service_interface import AnswerApprovalServiceInterface
from src.core.logging_config import get_logger
from src.domain.http.caller_domains import CallerMeta


logger = get_logger(__name__)


class ApproveAnswerController:
    """Controller para POST /reviews/approve-answer/{answer_uuid}"""
    
    def __init__(self, approval_service: AnswerApprovalServiceInterface):
        self.__approval_service = approval_service
    
    def handle(
        self,
        db: Session,
        answer_uuid: str,
        token_infos: Dict[str, Any],
        caller_meta: CallerMeta
    ) -> dict:
        """
        Aprova uma resposta individual, marcando como finalizada.
        
        Args:
            db: Sessão do banco de dados
            answer_uuid: UUID da resposta a ser aprovada
            token_infos: Informações do token JWT
            caller_meta: Metadados da chamada
            
        Returns:
            Dict com mensagem de sucesso e dados da resposta
        """
        
        user_uuid = token_infos.get("sub")
        if not user_uuid:
            logger.error("Token inválido: UUID do usuário não encontrado")
            raise ValueError("Token inválido")
        
        logger.info(
            "Aprovando resposta %s - Usuário: %s - IP: %s",
            answer_uuid,
            user_uuid,
            caller_meta.ip
        )
        
        response = self.__approval_service.approve_answer(
            db=db,
            answer_uuid=UUID(answer_uuid),
            user_uuid=UUID(user_uuid)
        )
        
        logger.info("Resposta aprovada com sucesso")
        
        return response
