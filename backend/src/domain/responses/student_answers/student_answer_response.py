from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class StudentAnswerResponse(BaseModel):
    """
    Modelo de resposta para resposta de aluno.
    """
    
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(
        ...,
        description="UUID da resposta",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova",
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )

    question_uuid: UUID = Field(
        ...,
        description="UUID da questão",
        examples=["123e4567-e89b-12d3-a456-426614174002"]
    )

    student_uuid: UUID = Field(
        ...,
        description="UUID do aluno",
        examples=["123e4567-e89b-12d3-a456-426614174003"]
    )

    answer: Optional[str] = Field(
        default=None,
        description="Resposta do aluno",
        examples=["Polimorfismo é a capacidade de objetos de classes diferentes responderem à mesma mensagem..."]
    )

    status: str = Field(
        ...,
        description="Status da resposta (SUBMITTED, GRADED, INVALID)",
        examples=["SUBMITTED"]
    )

    score: Optional[float] = Field(
        default=None,
        description="Pontuação obtida",
        examples=[8.5]
    )

    feedback: Optional[str] = Field(
        default=None,
        description="Feedback da correção",
        examples=["Boa resposta, mas poderia ter explicado melhor..."]
    )

    graded_at: Optional[datetime] = Field(
        default=None,
        description="Data/hora da correção",
        examples=["2024-01-15T10:30:00Z"]
    )

    graded_by: Optional[UUID] = Field(
        default=None,
        description="UUID do corretor",
        examples=["123e4567-e89b-12d3-a456-426614174004"]
    )

    is_graded: bool = Field(
        ...,
        description="Indica se a resposta já foi corrigida",
        examples=[False]
    )

    created_at: datetime = Field(
        ...,
        description="Data/hora de criação da resposta",
        examples=["2024-01-15T10:30:00Z"]
    )

    updated_at: datetime = Field(
        ...,
        description="Data/hora da última atualização da resposta",
        examples=["2024-01-15T10:30:00Z"]
    )
