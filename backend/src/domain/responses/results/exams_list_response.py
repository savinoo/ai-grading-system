"""
Response model para lista resumida de provas com resultados.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExamResultsSummaryResponse(BaseModel):
    """Resumo de uma prova com resultados para listagem."""
    
    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova"
    )
    exam_title: str = Field(
        ...,
        description="Título da prova",
        examples=["Prova 1 - POO"]
    )
    status: str = Field(
        ...,
        description="Status da correção: GRADED, PARTIAL, PENDING",
        examples=["GRADED"]
    )
    graded_at: Optional[datetime] = Field(
        None,
        description="Data/hora da conclusão da correção"
    )
    total_students: int = Field(
        ...,
        description="Total de alunos que responderam",
        examples=[32]
    )
    average_score: float = Field(
        ...,
        description="Média geral das notas",
        examples=[7.2]
    )
    arbiter_rate: float = Field(
        ...,
        description="Percentual de respostas que precisaram de árbitro",
        examples=[12.5]
    )
