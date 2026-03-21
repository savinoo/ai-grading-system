from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserLoginResponse(BaseModel):
    """Modelo de resposta para login de usuários."""
    
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str = Field(..., description="Token de acesso JWT")
    token_type: str = Field(default="Bearer", description="Tipo do token")
    expires_in: int = Field(..., description="Tempo de expiração em segundos")
    
    # Dados do usuário
    user_uuid: UUID = Field(..., description="UUID do usuário")
    email: EmailStr = Field(..., description="Email do usuário")
    user_type: str = Field(..., description="Tipo de usuário")
