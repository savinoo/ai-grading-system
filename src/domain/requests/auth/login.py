from __future__ import annotations

from pydantic import BaseModel, Field, EmailStr


class UserLoginRequest(BaseModel):
    """Modelo de requisição para login de usuários."""
    
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., description="Senha do usuário")
