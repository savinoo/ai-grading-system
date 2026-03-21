from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class ExamQuestionCriteriaOverrideCreateRequest(BaseModel):
    """
    Modelo de requisição para criação de sobrescrita de critério de questão.
    """

    question_uuid: UUID = Field(
        ...,
        description="UUID da questão",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    criteria_uuid: UUID = Field(
        ...,
        description="UUID do critério de avaliação",
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )

    weight_override: Optional[float] = Field(
        default=None,
        gt=0,
        description="Peso sobrescrito do critério (se definido, deve ser maior que 0)",
        examples=[1.5]
    )

    max_points_override: Optional[float] = Field(
        default=None,
        ge=0,
        description="Pontuação máxima sobrescrita (se definida, deve ser maior ou igual a 0)",
        examples=[10.0]
    )

    active: Optional[bool] = Field(
        default=None,
        description="Indica se a sobrescrita está ativa (false remove o critério da questão)",
        examples=[True]
    )

    @field_validator("weight_override")
    @classmethod
    def validate_weight_override(cls, value: Optional[float]) -> Optional[float]:
        """Valida se o peso sobrescrito é maior que 0."""
        if value is not None and value <= 0:
            raise ValueError("O peso sobrescrito deve ser maior que 0")
        return value

    @field_validator("max_points_override")
    @classmethod
    def validate_max_points_override(cls, value: Optional[float]) -> Optional[float]:
        """Valida se max_points_override, quando definido, é maior ou igual a 0."""
        if value is not None and value < 0:
            raise ValueError("A pontuação máxima sobrescrita deve ser maior ou igual a 0")
        return value
