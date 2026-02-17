"""
Interface para serviço de dashboard.
"""

from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.responses.dashboard.dashboard_stats_response import DashboardStatsResponse


class DashboardServiceInterface:
    """Interface para serviço de dashboard."""
    
    def get_teacher_dashboard_stats(
        self,
        db: Session,
        teacher_uuid: UUID,
        limit_recent_exams: int = 10
    ) -> DashboardStatsResponse:
        """
        Obtém estatísticas do dashboard para um professor.
        
        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor
            limit_recent_exams: Limite de provas recentes a retornar
            
        Returns:
            DashboardStatsResponse com todas as estatísticas
        """
        raise NotImplementedError()
