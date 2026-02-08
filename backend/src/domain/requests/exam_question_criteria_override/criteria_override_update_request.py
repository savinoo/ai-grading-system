from typing import Optional

from pydantic import BaseModel, Field, field_validator

class ExamQuestionCriteriaOverrideUpdateRequest(BaseModel):
    """
    Modelo de requisição para atualização de sobrescrita de critério de questão.
    """

    weight_override: Optional[float] = Field(
        default=None,
        gt=0,
        description="Novo peso sobrescrito do critério (se definido, deve ser maior que 0)",
        examples=[1.5]
    )

    max_points_override: Optional[float] = Field(
        default=None,
        ge=0,
        description="Nova pontuação máxima sobrescrita (se definida, deve ser maior ou igual a 0)",
        examples=[10.0]
    )

    active: Optional[bool] = Field(
        default=None,
        description="Status ativo/inativo da sobrescrita",
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
