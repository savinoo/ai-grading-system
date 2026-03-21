from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.core.settings import settings


class AttachmentUploadRequest(BaseModel):
    """
    Modelo de requisição para upload de anexo.
    Nota: Este modelo é usado internamente. O arquivo em si vem do FastAPI UploadFile.
    """

    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova à qual o anexo será vinculado",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    original_filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
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
        gt=0,
        description="Tamanho do arquivo em bytes",
        examples=[1048576]
    )

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """
        Valida se o tipo MIME está na lista de tipos permitidos.
        """
        allowed_types = settings.ALLOWED_MIME_TYPES
        
        if v not in allowed_types:
            raise ValueError(
                f"Tipo MIME '{v}' não permitido. "
                f"Tipos permitidos: {', '.join(allowed_types)}"
            )
        
        return v

    @field_validator("size_bytes")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """
        Valida se o tamanho do arquivo não excede o limite.
        """
        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        
        if v > max_size_bytes:
            raise ValueError(
                f"Arquivo muito grande ({v} bytes). "
                f"Tamanho máximo permitido: {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "exam_uuid": "123e4567-e89b-12d3-a456-426614174000",
                "original_filename": "prova_matematica.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 1048576
            }
        }
    }
