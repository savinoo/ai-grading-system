from datetime import datetime
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class AttachmentUploadResponse(BaseModel):
    """
    Modelo de resposta para upload de anexo.
    Retorna informações do anexo criado.
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
        description="Hash SHA256 do arquivo para verificação de integridade",
        examples=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]
    )

    vector_status: Literal["DRAFT", "SUCCESS", "FAILED"] = Field(
        default="DRAFT",
        description="Status do processamento no banco vetorial. DRAFT: aguardando processamento, SUCCESS: processado com sucesso, FAILED: falha no processamento",
        examples=["DRAFT"]
    )

    file_path: str = Field(
        ...,
        description="Caminho relativo do arquivo no servidor",
        examples=["123e4567-e89b-12d3-a456-426614174000/987e6543-e21b-12d3-a456-426614174000.pdf"]
    )

    created_at: datetime = Field(
        ...,
        description="Data e hora do upload",
        examples=["2026-01-15T10:30:00"]
    )

    message: str = Field(
        default="Arquivo enviado com sucesso",
        description="Mensagem de sucesso",
        examples=["Arquivo enviado com sucesso"]
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
                "file_path": "987e6543-e21b-12d3-a456-426614174000/123e4567-e89b-12d3-a456-426614174000.pdf",
                "created_at": "2026-01-15T10:30:00",
                "message": "Arquivo enviado com sucesso"
            }
        }
    )
