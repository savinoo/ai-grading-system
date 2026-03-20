from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ClassCreateRequest(BaseModel):
    """
    Modelo de requisição para criação de turma.
    """
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nome da turma",
        examples=["Matemática Avançada - Turma A"]
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Descrição da turma",
        examples=["Turma de matemática avançada para o 3º ano"]
    )
    
    year: Optional[int] = Field(
        default=None,
        description="Ano letivo",
        examples=[2026]
    )
    
    semester: Optional[int] = Field(
        default=None,
        description="Semestre (1 ou 2)",
        examples=[1]
    )
    
    @field_validator("semester")
    @classmethod
    def validate_semester(cls, v: Optional[int]) -> Optional[int]:
        """
        Valida o semestre.
        
        Args:
            v: Semestre a ser validado
            
        Returns:
            Optional[int]: Semestre validado
            
        Raises:
            ValueError: Se o semestre não for 1 ou 2
        """
        if v is not None and v not in [1, 2]:
            raise ValueError("O semestre deve ser 1 ou 2.")
        return v
    
    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        """
        Valida o ano.
        
        Args:
            v: Ano a ser validado
            
        Returns:
            Optional[int]: Ano validado
            
        Raises:
            ValueError: Se o ano for inválido
        """
        if v is not None and (v < 2000 or v > 2100):
            raise ValueError("O ano deve estar entre 2000 e 2100.")
        return v
