"""
Schemas core para questões, critérios e metadados de avaliação.
Usados por serviços RAG e agentes corretores.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class QuestionMetadata(BaseModel):
    """
    Metadados para filtragem avançada no RAG.
    Permite buscar contexto específico por disciplina e tópico.
    """
    
    discipline: str = Field(
        ...,
        description="Disciplina da questão (ex: Estrutura de Dados, Algoritmos)",
        min_length=1
    )
    topic: str = Field(
        ...,
        description="Tópico específico (ex: Árvores Binárias, Ordenação)",
        min_length=1
    )
    difficulty_level: Optional[str] = Field(
        default=None,
        description="Nível de dificuldade (fácil, médio, difícil)"
    )
    
    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        """Valida que difficulty_level está entre os valores aceitos."""
        if v is None:
            return v
        
        allowed = {'fácil', 'facil', 'médio', 'medio', 'difícil', 'dificil'}
        if v.lower() not in allowed:
            raise ValueError(f"difficulty_level deve ser um de: {allowed}")
        
        return v.lower()


class EvaluationCriterion(BaseModel):
    """
    Define um critério específico da rubrica de avaliação.
    Usado para avaliar aspectos individuais da resposta do aluno.
    """
    
    name: str = Field(
        ...,
        description="Nome do critério (ex: Precisão Conceitual, Completude)",
        min_length=1
    )
    description: str = Field(
        ...,
        description="Descrição detalhada do que é esperado neste critério",
        min_length=1
    )
    weight: float = Field(
        1.0,
        description="Peso deste critério na nota final (multiplicador)",
        gt=0.0
    )
    max_score: float = Field(
        10.0,
        description="Nota máxima possível para este critério",
        gt=0.0
    )
    
    @field_validator('max_score')
    @classmethod
    def validate_max_score(cls, v: float) -> float:
        """Garante que max_score não seja absurdamente alto."""
        if v > 100.0:
            raise ValueError("max_score não pode ser maior que 100.0")
        return v


class ExamQuestion(BaseModel):
    """
    Estrutura completa de uma questão de prova.
    Combina enunciado, rubrica e metadados para avaliação.
    """
    
    id: UUID = Field(
        ...,
        description="Identificador único da questão (UUID)"
    )
    statement: str = Field(
        ...,
        description="O enunciado completo da questão",
        min_length=10
    )
    rubric: List[EvaluationCriterion] = Field(
        ...,
        description="Critérios de avaliação definidos pelo professor",
        min_length=1
    )
    metadata: QuestionMetadata = Field(
        ...,
        description="Metadados para contexto e busca RAG"
    )
    
    @field_validator('rubric')
    @classmethod
    def validate_rubric_weights(cls, v: List[EvaluationCriterion]) -> List[EvaluationCriterion]:
        """Valida que a soma dos pesos é razoável."""
        total_weight = sum(criterion.weight for criterion in v)
        if total_weight <= 0:
            raise ValueError("Soma dos pesos deve ser maior que zero")
        return v


class StudentAnswer(BaseModel):
    """
    Input: Resposta estruturada do aluno para uma questão.
    Usada como input principal para o workflow de correção.
    """
    
    id: Optional[UUID] = Field(
        default=None,
        description="UUID da resposta (se já existir no banco)"
    )
    student_id: UUID = Field(
        ...,
        description="UUID do estudante (foreign key)"
    )
    question_id: UUID = Field(
        ...,
        description="UUID da questão respondida"
    )
    text: str = Field(
        ...,
        description="A resposta discursiva do aluno",
        min_length=1
    )
    
    @field_validator('text')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Garante que a resposta não é apenas espaços em branco."""
        if not v.strip():
            raise ValueError("Resposta não pode ser vazia ou apenas espaços")
        return v.strip()
