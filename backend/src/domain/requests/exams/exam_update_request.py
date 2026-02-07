from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class ExamUpdateRequest(BaseModel):
    """
    Modelo de requisição para atualização de prova.
    Apenas campos editáveis: title, description e class_uuid.
    """

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Título da prova",
        examples=["Prova de Matemática - 1º Bimestre (Atualizado)"]
    )

    description: Optional[str] = Field(
        default=None,
        description="Descrição da prova",
        examples=["Prova abrangendo conteúdos de álgebra e geometria avançada"]
    )

    class_uuid: Optional[UUID] = Field(
        default=None,
        description="UUID da turma",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    @field_validator("title", "description", "class_uuid", mode="before")
    @classmethod
    def validate_fields(cls, v):
        """
        Valida os campos da requisição.
        """
        return v

    def has_any_field(self) -> bool:
        """
        Verifica se pelo menos um campo foi fornecido.
        
        Returns:
            bool: True se pelo menos um campo foi fornecido
        """
        return self.title is not None or self.description is not None or self.class_uuid is not None
