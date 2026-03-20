from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class UserResponse(BaseModel):
    """
    Modelo de resposta para dados de usuário.
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "email": "usuario@exemplo.com",
                "created_at": "2026-01-10T10:00:00"
            }
        }
    )
    
    uuid: UUID = Field(
        ...,
        description="UUID do usuário",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    
    email: str = Field(
        ...,
        description="Email do usuário",
        examples=["usuario@exemplo.com"]
    )
        
    created_at: datetime = Field(
        ...,
        description="Data e hora de criação",
        examples=["2026-01-10T10:00:00"]
    )
