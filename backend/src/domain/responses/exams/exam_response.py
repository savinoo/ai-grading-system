from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class ExamResponse(BaseModel):
    """
    Modelo de resposta para uma prova individual.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Prova de Matemática - 1º Bimestre",
                "description": "Prova abrangendo conteúdos de álgebra e geometria",
                "class_uuid": "987e6543-e21b-12d3-a456-426614174000",
                "status": "DRAFT",
                "starts_at": "2026-03-15T08:00:00",
                "ends_at": "2026-03-15T10:00:00",
                "active": True,
                "created_at": "2026-02-07T10:00:00",
                "updated_at": "2026-02-07T10:00:00"
            }
        }
    )

    uuid: UUID = Field(
        ...,
        description="UUID da prova",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    title: str = Field(
        ...,
        description="Título da prova",
        examples=["Prova de Matemática - 1º Bimestre"]
    )

    description: Optional[str] = Field(
        default=None,
        description="Descrição da prova"
    )

    class_uuid: Optional[UUID] = Field(
        default=None,
        description="UUID da turma"
    )

    status: str = Field(
        ...,
        description="Status da prova (DRAFT, PUBLISHED, ARCHIVED, FINISHED)"
    )

    starts_at: Optional[datetime] = Field(
        default=None,
        description="Data/hora de início da prova"
    )

    ends_at: Optional[datetime] = Field(
        default=None,
        description="Data/hora de término da prova"
    )

    active: bool = Field(
        ...,
        description="Se a prova está ativa"
    )

    created_at: datetime = Field(
        ...,
        description="Data/hora de criação"
    )

    updated_at: datetime = Field(
        ...,
        description="Data/hora de última atualização"
    )
