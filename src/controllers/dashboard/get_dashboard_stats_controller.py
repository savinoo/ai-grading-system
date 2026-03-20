"""
Controller para buscar estatísticas do dashboard.
"""

from uuid import UUID
from typing import Any, Dict
from sqlalchemy.orm import Session

from src.interfaces.services.dashboard.dashboard_service_interface import DashboardServiceInterface
from src.domain.responses.dashboard.dashboard_stats_response import DashboardStatsResponse
from src.domain.http.caller_domains import CallerMeta
from src.core.logging_config import get_logger


logger = get_logger(__name__)


class GetDashboardStatsController:
    """Controller para GET /dashboard/stats/{teacher_uuid}"""
    
    def __init__(self, dashboard_service: DashboardServiceInterface):
        self.__dashboard_service = dashboard_service
    
    def handle(
        self,
        db: Session,
        teacher_uuid: UUID,
        limit_recent_exams: int,
        token_infos: Dict[str, Any],
        caller_meta: CallerMeta
    ) -> DashboardStatsResponse:
        """
        Busca estatísticas do dashboard do professor.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            limit_recent_exams: Limite de provas recentes
            token_infos: Informações do token JWT
            caller_meta: Metadados da chamada
            
        Returns:
            DashboardStatsResponse com estatísticas
        """
        
        user_uuid = token_infos.get("sub")
        if not user_uuid:
            logger.error("Token inválido: UUID do usuário não encontrado")
            raise ValueError("Token inválido")
        
        if str(user_uuid) != str(teacher_uuid):
            logger.error("Usuário %s tentou acessar dashboard de %s", user_uuid, teacher_uuid)
            raise ValueError("Não autorizado a acessar este dashboard")
        
        logger.info(
            "Buscando estatísticas do dashboard para professor %s - IP: %s",
            teacher_uuid,
            caller_meta.ip
        )
        
        response = self.__dashboard_service.get_teacher_dashboard_stats(
            db=db,
            teacher_uuid=teacher_uuid,
            limit_recent_exams=limit_recent_exams
        )
        
        logger.info(
            "Estatísticas retornadas: %d provas totais, %d respostas",
            response.exam_stats.total,
            response.answer_stats.total
        )
        
        return response
