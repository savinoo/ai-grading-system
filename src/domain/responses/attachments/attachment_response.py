from datetime import datetime
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class AttachmentResponse(BaseModel):
    """
    Modelo de resposta para anexo.
    """

    id: int = Field(
        ...,
        description="ID do anexo",
        examples=[1]
    )

    uuid: UUID = Field(
        ...,
        description="UUID do anexo",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    original_filename: str = Field(
        ...,
        description="Nome original do arquivo",
        examples=["prova_matematica.pdf"]
    )

    mime_type: str = Field(
        ...,
        description="Tipo MIME do arquivo",
        examples=["application/pdf"]
    )

    size_bytes: int = Field(
        ...,
        description="Tamanho do arquivo em bytes",
        examples=[1048576]
    )

    sha256_hash: str = Field(
        ...,
        description="Hash SHA256 do arquivo",
        examples=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]
    )

    vector_status: Literal["DRAFT", "SUCCESS", "FAILED"] = Field(
        default="DRAFT",
        description="Status do processamento no banco vetorial. DRAFT: aguardando processamento, SUCCESS: processado com sucesso, FAILED: falha no processamento",
        examples=["DRAFT"]
    )

    created_at: datetime = Field(
        ...,
        description="Data e hora de criação",
        examples=["2026-01-15T10:30:00"]
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "exam_uuid": "987e6543-e21b-12d3-a456-426614174000",
                "original_filename": "prova_matematica.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 1048576,
                "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "vector_status": "DRAFT",
                "created_at": "2026-01-15T10:30:00"
            }
        }
    )
