from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class ExamQuestionResponse(BaseModel):
    """
    Modelo de resposta para questão de prova.
    """
    
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(
        ...,
        description="UUID da questão",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova",
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )

    question_order: int = Field(
        ...,
        description="Ordem da questão na prova",
        examples=[1]
    )

    statement: str = Field(
        ...,
        description="Enunciado da questão",
        examples=["Explique o conceito de polimorfismo em programação orientada a objetos."]
    )

    points: float = Field(
        ...,
        description="Pontuação da questão",
        examples=[10.0]
    )

    active: bool = Field(
        ...,
        description="Indica se a questão está ativa",
        examples=[True]
    )

    is_graded: bool = Field(
        ...,
        description="Indica se a questão já foi corrigida",
        examples=[False]
    )

    created_at: datetime = Field(
        ...,
        description="Data/hora de criação da questão",
        examples=["2024-01-15T10:30:00Z"]
    )

    updated_at: datetime = Field(
        ...,
        description="Data/hora da última atualização da questão",
        examples=["2024-01-15T10:30:00Z"]
    )
