"""
Interface para o serviço de análise pedagógica.
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.responses.analytics import (
    ClassAnalyticsResponse,
    ClassAnalyticsSummaryResponse,
    StudentPerformanceResponse,
)


class AnalyticsServiceInterface(ABC):
    """Interface para serviço de análise pedagógica de alunos e turmas."""

    @abstractmethod
    def get_class_analytics(
        self,
        db: Session,
        class_uuid: UUID,
        teacher_uuid: UUID,
    ) -> ClassAnalyticsResponse:
        """
        Retorna a análise pedagógica completa de uma turma.

        Args:
            db: Sessão do banco de dados
            class_uuid: UUID da turma
            teacher_uuid: UUID do professor (para validação de acesso)

        Returns:
            ClassAnalyticsResponse com métricas, outliers e gaps mais comuns

        Raises:
            NotFoundError: Se a turma não existir
            ForbiddenError: Se o professor não tiver acesso à turma
        """

    @abstractmethod
    def list_classes_analytics(
        self,
        db: Session,
        teacher_uuid: UUID,
    ) -> List[ClassAnalyticsSummaryResponse]:
        """
        Retorna sumário analítico de todas as turmas do professor.

        Args:
            db: Sessão do banco de dados
            teacher_uuid: UUID do professor

        Returns:
            Lista de ClassAnalyticsSummaryResponse ordenada por número de alunos em dificuldade
        """

    @abstractmethod
    def get_student_performance(
        self,
        db: Session,
        student_uuid: UUID,
        class_uuid: UUID,
        teacher_uuid: UUID,
    ) -> StudentPerformanceResponse:
        """
        Retorna o perfil de desempenho individual de um aluno em uma turma.

        Args:
            db: Sessão do banco de dados
            student_uuid: UUID do aluno
            class_uuid: UUID da turma (contexto de análise)
            teacher_uuid: UUID do professor (para validação de acesso)

        Returns:
            StudentPerformanceResponse com perfil completo, gaps e tendência

        Raises:
            NotFoundError: Se o aluno ou turma não existir
        """
