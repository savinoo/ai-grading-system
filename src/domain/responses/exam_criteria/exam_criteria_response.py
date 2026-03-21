from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class ExamCriteriaResponse(BaseModel):
    """
    Modelo de resposta para critérios de prova.
    """
    
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(
        ...,
        description="UUID do critério de prova",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova",
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )

    criteria_uuid: UUID = Field(
        ...,
        description="UUID do critério de avaliação",
        examples=["123e4567-e89b-12d3-a456-426614174002"]
    )

    weight: float = Field(
        ...,
        description="Peso do critério",
        examples=[1.5]
    )

    max_points: Optional[float] = Field(
        default=None,
        description="Pontuação máxima do critério",
        examples=[10.0]
    )

    active: bool = Field(
        ...,
        description="Indica se o critério está ativo",
        examples=[True]
    )

    created_at: datetime = Field(
        ...,
        description="Data de criação do critério de prova",
        examples=["2026-01-01T10:00:00Z"]
    )

    # Campos do GradingCriteria (via JOIN ou relacionamento)
    grading_criteria_name: Optional[str] = Field(
        default=None,
        description="Nome do critério de avaliação",
        examples=["Clareza"]
    )

    grading_criteria_description: Optional[str] = Field(
        default=None,
        description="Descrição do critério de avaliação",
        examples=["Avalia a clareza na comunicação das ideias"]
    )
