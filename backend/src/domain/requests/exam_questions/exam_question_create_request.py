from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class ExamQuestionCreateRequest(BaseModel):
    """
    Modelo de requisição para criação de questão de prova.
    """

    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    statement: str = Field(
        ...,
        min_length=1,
        description="Enunciado da questão",
        examples=["Explique o conceito de polimorfismo em programação orientada a objetos."]
    )

    question_order: int = Field(
        ...,
        ge=1,
        description="Ordem da questão na prova (deve ser maior ou igual a 1)",
        examples=[1]
    )

    points: float = Field(
        default=1.0,
        ge=0,
        description="Pontuação da questão (deve ser maior ou igual a 0)",
        examples=[10.0]
    )

    @field_validator("statement")
    @classmethod
    def validate_statement(cls, value: str) -> str:
        """Valida se o enunciado não está vazio."""
        if not value.strip():
            raise ValueError("O enunciado da questão não pode estar vazio")
        return value.strip()

    @field_validator("question_order")
    @classmethod
    def validate_question_order(cls, value: int) -> int:
        """Valida se a ordem da questão é maior ou igual a 1."""
        if value < 1:
            raise ValueError("A ordem da questão deve ser maior ou igual a 1")
        return value

    @field_validator("points")
    @classmethod
    def validate_points(cls, value: float) -> float:
        """Valida se a pontuação é maior ou igual a 0."""
        if value < 0:
            raise ValueError("A pontuação deve ser maior ou igual a 0")
        return value
