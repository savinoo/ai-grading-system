from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class ExamQuestionCriteriaOverrideResponse(BaseModel):
    """
    Modelo de resposta para sobrescrita de critério de questão.
    """
    
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(
        ...,
        description="UUID da sobrescrita",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    question_uuid: UUID = Field(
        ...,
        description="UUID da questão",
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )

    criteria_uuid: UUID = Field(
        ...,
        description="UUID do critério de avaliação",
        examples=["123e4567-e89b-12d3-a456-426614174002"]
    )

    weight_override: Optional[float] = Field(
        default=None,
        description="Peso sobrescrito do critério",
        examples=[1.5]
    )

    max_points_override: Optional[float] = Field(
        default=None,
        description="Pontuação máxima sobrescrita",
        examples=[10.0]
    )

    active: bool = Field(
        ...,
        description="Indica se a sobrescrita está ativa",
        examples=[True]
    )

    created_at: datetime = Field(
        ...,
        description="Data/hora de criação da sobrescrita",
        examples=["2024-01-15T10:30:00Z"]
    )
