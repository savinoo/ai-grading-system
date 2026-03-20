"""
Response models para estatísticas do dashboard.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class ExamStatsCount(BaseModel):
    """Contadores de provas por status."""
    model_config = ConfigDict(from_attributes=True)
    
    draft: int = Field(..., description="Total de provas em rascunho")
    active: int = Field(..., description="Total de provas ativas")
    grading: int = Field(..., description="Total de provas em correção")
    graded: int = Field(..., description="Total de provas corrigidas")
    finalized: int = Field(..., description="Total de provas finalizadas")
    total: int = Field(..., description="Total de provas")


class AnswerStatsCount(BaseModel):
    """Contadores de respostas."""
    model_config = ConfigDict(from_attributes=True)
    
    total: int = Field(..., description="Total de respostas")
    pending: int = Field(..., description="Respostas aguardando correção")
    graded: int = Field(..., description="Respostas corrigidas")
    pending_review: int = Field(..., description="Respostas aguardando revisão do professor")


class RecentExam(BaseModel):
    """Dados resumidos de uma prova recente."""
    model_config = ConfigDict(from_attributes=True)
    
    uuid: UUID = Field(..., description="UUID da prova")
    title: str = Field(..., description="Título da prova")
    class_name: Optional[str] = Field(None, description="Nome da turma")
    status: str = Field(..., description="Status da prova")
    starts_at: Optional[datetime] = Field(None, description="Data de início")
    ends_at: Optional[datetime] = Field(None, description="Data de término")
    total_questions: int = Field(..., description="Total de questões")
    total_students: int = Field(0, description="Total de alunos matriculados")
    answers_submitted: int = Field(0, description="Respostas submetidas")
    answers_graded: int = Field(0, description="Respostas corrigidas")
    pending_review: int = Field(0, description="Respostas aguardando revisão")
    created_at: datetime = Field(..., description="Data de criação")


class PendingAction(BaseModel):
    """Ação pendente para o professor."""
    model_config = ConfigDict(from_attributes=True)
    
    type: str = Field(..., description="Tipo de ação: draft, review, grading")
    exam_uuid: UUID = Field(..., description="UUID da prova")
    exam_title: str = Field(..., description="Título da prova")
    description: str = Field(..., description="Descrição da ação")
    count: int = Field(0, description="Quantidade de itens pendentes")
    priority: str = Field("normal", description="Prioridade: high, normal, low")
    created_at: Optional[datetime] = Field(None, description="Data de criação")


class DashboardStatsResponse(BaseModel):
    """Resposta completa com estatísticas do dashboard."""
    model_config = ConfigDict(from_attributes=True)
    
    exam_stats: ExamStatsCount = Field(..., description="Estatísticas de provas")
    answer_stats: AnswerStatsCount = Field(..., description="Estatísticas de respostas")
    recent_exams: List[RecentExam] = Field(default_factory=list, description="Provas recentes")
    pending_actions: List[PendingAction] = Field(default_factory=list, description="Ações pendentes")
