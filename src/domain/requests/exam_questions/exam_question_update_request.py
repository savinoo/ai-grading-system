from typing import Optional

from pydantic import BaseModel, Field, field_validator

class ExamQuestionUpdateRequest(BaseModel):
    """
    Modelo de requisição para atualização de questão de prova.
    """

    statement: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Novo enunciado da questão",
        examples=["Explique o conceito de polimorfismo em programação orientada a objetos."]
    )

    question_order: Optional[int] = Field(
        default=None,
        ge=1,
        description="Nova ordem da questão na prova (deve ser maior ou igual a 1)",
        examples=[1]
    )

    points: Optional[float] = Field(
        default=None,
        ge=0,
        description="Nova pontuação da questão (deve ser maior ou igual a 0)",
        examples=[10.0]
    )

    active: Optional[bool] = Field(
        default=None,
        description="Status ativo/inativo da questão",
        examples=[True]
    )

    @field_validator("statement")
    @classmethod
    def validate_statement(cls, value: Optional[str]) -> Optional[str]:
        """Valida se o enunciado não está vazio."""
        if value is not None and not value.strip():
            raise ValueError("O enunciado da questão não pode estar vazio")
        return value.strip() if value else None

    @field_validator("question_order")
    @classmethod
    def validate_question_order(cls, value: Optional[int]) -> Optional[int]:
        """Valida se a ordem da questão é maior ou igual a 1."""
        if value is not None and value < 1:
            raise ValueError("A ordem da questão deve ser maior ou igual a 1")
        return value

    @field_validator("points")
    @classmethod
    def validate_points(cls, value: Optional[float]) -> Optional[float]:
        """Valida se a pontuação é maior ou igual a 0."""
        if value is not None and value < 0:
            raise ValueError("A pontuação deve ser maior ou igual a 0")
        return value
