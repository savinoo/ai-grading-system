from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class GradingCriteriaResponse(BaseModel):
    """
    Modelo de resposta para critérios de avaliação.
    """
    
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(
        ...,
        description="UUID do critério",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    code: str = Field(
        ...,
        description="Código único do critério",
        examples=["COHERENCE"]
    )

    name: str = Field(
        ...,
        description="Nome do critério",
        examples=["Coerência"]
    )

    description: Optional[str] = Field(
        default=None,
        description="Descrição do critério",
        examples=["Avalia a coerência e lógica da resposta"]
    )

    active: bool = Field(
        ...,
        description="Indica se o critério está ativo",
        examples=[True]
    )

    created_at: datetime = Field(
        ...,
        description="Data de criação do critério",
        examples=["2026-01-01T10:00:00Z"]
    )
