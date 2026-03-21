from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

class StudentAnswerCreateRequest(BaseModel):
    """
    Modelo de requisição para criação de resposta de aluno.
    """

    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    question_uuid: UUID = Field(
        ...,
        description="UUID da questão",
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )

    student_uuid: UUID = Field(
        ...,
        description="UUID do aluno",
        examples=["123e4567-e89b-12d3-a456-426614174002"]
    )

    answer_text: Optional[str] = Field(
        default=None,
        description="Resposta do aluno para a questão",
        examples=["Polimorfismo é a capacidade de objetos de classes diferentes responderem à mesma mensagem..."]
    )
