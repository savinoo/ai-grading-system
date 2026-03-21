from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class ExamCreateRequest(BaseModel):
    """
    Modelo de requisição para criação de prova.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Título da prova",
        examples=["Prova de Matemática - 1º Bimestre"]
    )

    description: Optional[str] = Field(
        default=None,
        description="Descrição da prova",
        examples=["Prova abrangendo conteúdos de álgebra e geometria"]
    )

    class_uuid: Optional[UUID] = Field(
        default=None,
        description="UUID da turma",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    status: str = Field(
        default="DRAFT",
        description="Status da prova",
        examples=["DRAFT"]
    )

    starts_at: Optional[datetime] = Field(
        default=None,
        description="Data/hora de início da prova",
        examples=["2026-03-15T08:00:00"]
    )

    ends_at: Optional[datetime] = Field(
        default=None,
        description="Data/hora de término da prova",
        examples=["2026-03-15T10:00:00"]
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """
        Valida o status da prova.
        
        Args:
            v: Status a ser validado
            
        Returns:
            str: Status validado
            
        Raises:
            ValueError: Se o status não for válido
        """
        valid_statuses = ["DRAFT", "PUBLISHED", "ARCHIVED", "FINISHED"]
        if v not in valid_statuses:
            raise ValueError(f"Status inválido. Valores permitidos: {', '.join(valid_statuses)}")
        return v

    @field_validator("ends_at")
    @classmethod
    def validate_exam_window(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """
        Valida se a data de término é posterior à data de início.
        
        Args:
            v: Data de término
            info: Contexto de validação
            
        Returns:
            Optional[datetime]: Data de término validada
            
        Raises:
            ValueError: Se a data de término for anterior à data de início
        """
        starts_at = info.data.get("starts_at")
        if v is not None and starts_at is not None and v <= starts_at:
            raise ValueError("A data de término deve ser posterior à data de início")
        return v
