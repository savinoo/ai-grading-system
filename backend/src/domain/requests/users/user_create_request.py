from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreateRequest(BaseModel):
    """
    Modelo de requisição para criação de usuário.
    """
    
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nome do usuário",
        examples=["João"]
    )
    
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Sobrenome do usuário",
        examples=["Silva"]
    )
    
    email: EmailStr = Field(
        ...,
        description="Email do usuário",
        examples=["usuario@exemplo.com"]
    )
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Senha do usuário (mínimo 8 caracteres)",
        examples=["SenhaSegura@123"]
    )
    
    user_type: Optional[str] = Field(
        default="teacher",
        description="Tipo de usuário (admin, teacher, student)",
        examples=["teacher", "student"]
    )
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Valida a força da senha.
        
        Args:
            v: Senha a ser validada
            
        Returns:
            str: Senha validada
            
        Raises:
            ValueError: Se a senha não atender aos requisitos
        """
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        
        if not any(char.isupper() for char in v):
            raise ValueError("Senha deve conter pelo menos uma letra maiúscula")
        
        if not any(char.islower() for char in v):
            raise ValueError("Senha deve conter pelo menos uma letra minúscula")
        
        if not any(char.isdigit() for char in v):
            raise ValueError("Senha deve conter pelo menos um número")
        
        return v
    
    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, v: Optional[str]) -> str:
        """
        Valida o tipo de usuário.
        
        Args:
            v: Tipo de usuário
            
        Returns:
            str: Tipo de usuário validado
            
        Raises:
            ValueError: Se o tipo não for válido
        """
        if v is None:
            return "student"
        
        allowed_types = ["admin", "teacher", "student"]
        if v not in allowed_types:
            raise ValueError(f"Tipo de usuário deve ser um de: {', '.join(allowed_types)}")
        
        return v
    
    class Config:
        """Configuração do modelo Pydantic."""
        json_schema_extra = {
            "example": {
                "first_name": "João",
                "last_name": "Silva",
                "email": "usuario@exemplo.com",
                "password": "SenhaSegura@123",
                "user_type": "teacher"
            }
        }
