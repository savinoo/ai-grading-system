from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class StudentInClass(BaseModel):
    """
    Representa um aluno em uma turma.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    uuid: UUID = Field(
        ...,
        description="UUID do aluno"
    )
    
    full_name: str = Field(
        ...,
        description="Nome completo do aluno"
    )
    
    email: Optional[str] = Field(
        default=None,
        description="Email do aluno"
    )
    
    enrolled_at: datetime = Field(
        ...,
        description="Data de matrícula na turma"
    )
    
    active: bool = Field(
        ...,
        description="Se a matrícula está ativa"
    )

class ClassWithStudentsResponse(BaseModel):
    """
    Modelo de resposta para turma com seus alunos.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Matemática Avançada - Turma A",
                "description": "Turma de matemática avançada",
                "year": 2026,
                "semester": 1,
                "total_students": 25,
                "students": [
                    {
                        "uuid": "223e4567-e89b-12d3-a456-426614174001",
                        "full_name": "João Silva",
                        "email": "joao@email.com",
                        "enrolled_at": "2026-01-13T10:00:00",
                        "active": True
                    }
                ]
            }
        }
    )
    
    uuid: UUID = Field(
        ...,
        description="UUID da turma"
    )
    
    name: str = Field(
        ...,
        description="Nome da turma"
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Descrição da turma"
    )
    
    year: Optional[int] = Field(
        default=None,
        description="Ano letivo"
    )
    
    semester: Optional[int] = Field(
        default=None,
        description="Semestre"
    )
    
    total_students: int = Field(
        ...,
        description="Total de alunos na turma"
    )
    
    students: List[StudentInClass] = Field(
        default_factory=list,
        description="Lista de alunos da turma"
    )
