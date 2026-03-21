from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ClassCreateResponse(BaseModel):
    """
    Modelo de resposta para criação de turma.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Matemática Avançada - Turma A",
                "description": "Turma de matemática avançada",
                "year": 2026,
                "semester": 1,
                "created_at": "2026-01-13T10:00:00"
            }
        }
    )
    
    uuid: UUID = Field(
        ...,
        description="UUID da turma",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    
    name: str = Field(
        ...,
        description="Nome da turma",
        examples=["Matemática Avançada - Turma A"]
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Descrição da turma"
    )
    
    year: Optional[int] = Field(
        default=None,
        description="Ano letivo"
    )
    
    semester: Optional[int] = Field(
        default=None,
        description="Semestre"
    )
    
    created_at: datetime = Field(
        ...,
        description="Data e hora de criação da turma",
        examples=["2026-01-13T10:00:00"]
    )
