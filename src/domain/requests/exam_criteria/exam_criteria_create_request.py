from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class ExamCriteriaCreateRequest(BaseModel):
    """
    Modelo de requisição para criação de critério de prova.
    """

    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    criteria_uuid: UUID = Field(
        ...,
        description="UUID do critério de avaliação",
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )

    weight: float = Field(
        default=1.0,
        gt=0,
        description="Peso do critério (deve ser maior que 0)",
        examples=[1.5]
    )

    max_points: Optional[float] = Field(
        default=None,
        ge=0,
        description="Pontuação máxima do critério (se definida, deve ser maior ou igual a 0)",
        examples=[10.0]
    )

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, value: float) -> float:
        """Valida se o peso é maior que 0."""
        if value <= 0:
            raise ValueError("O peso deve ser maior que 0")
        return value

    @field_validator("max_points")
    @classmethod
    def validate_max_points(cls, value: Optional[float]) -> Optional[float]:
        """Valida se max_points, quando definido, é maior ou igual a 0."""
        if value is not None and value < 0:
            raise ValueError("A pontuação máxima deve ser maior ou igual a 0")
        return value
