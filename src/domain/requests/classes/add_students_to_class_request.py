from typing import List
from pydantic import BaseModel, EmailStr, Field

class StudentData(BaseModel):
    """
    Dados de um aluno para adicionar à turma.
    """
    
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=250,
        description="Nome completo do aluno",
        examples=["João Silva"]
    )
    
    email: EmailStr | None = Field(
        default=None,
        description="Email do aluno (usado para validar se já existe)",
        examples=["aluno@exemplo.com"]
    )

class AddStudentsToClassRequest(BaseModel):
    """
    Modelo de requisição para adicionar alunos a uma turma.
    """
    
    students: List[StudentData] = Field(
        ...,
        min_length=1,
        description="Lista de alunos a serem adicionados",
        examples=[[
            {"full_name": "João Silva", "email": "joao@email.com"},
            {"full_name": "Maria Santos", "email": None}
        ]]
    )
