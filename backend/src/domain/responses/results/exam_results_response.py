"""
Response models para resultados de provas corrigidas.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ScoreDistribution(BaseModel):
    """Distribuição de notas por faixa."""
    
    range: str = Field(
        ...,
        description="Faixa de notas (ex: '0-2', '2-4', etc.)",
        examples=["8-10"]
    )
    count: int = Field(
        ...,
        description="Número de alunos nesta faixa",
        examples=[12]
    )


class QuestionStatistics(BaseModel):
    """Estatísticas de uma questão específica."""
    
    question_uuid: UUID = Field(
        ...,
        description="UUID da questão"
    )
    question_number: int = Field(
        ...,
        description="Número da questão",
        examples=[1]
    )
    question_title: str = Field(
        ...,
        description="Título ou enunciado resumido da questão",
        examples=["Explique o conceito de Polimorfismo"]
    )
    average_score: float = Field(
        ...,
        description="Média das notas nesta questão",
        examples=[7.8]
    )
    std_deviation: float = Field(
        ...,
        description="Desvio padrão das notas",
        examples=[1.5]
    )
    max_score: float = Field(
        ...,
        description="Pontuação máxima possível",
        examples=[10.0]
    )
    min_score: float = Field(
        ...,
        description="Menor nota obtida",
        examples=[2.5]
    )
    arbiter_count: int = Field(
        ...,
        description="Número de respostas que precisaram de árbitro",
        examples=[5]
    )


class ExamStatistics(BaseModel):
    """Estatísticas gerais da prova."""
    
    total_students: int = Field(
        ...,
        description="Total de alunos que responderam",
        examples=[32]
    )
    total_questions: int = Field(
        ...,
        description="Total de questões da prova",
        examples=[4]
    )
    arbiter_rate: float = Field(
        ...,
        description="Percentual de respostas que precisaram de árbitro",
        examples=[12.5]
    )
    average_score: float = Field(
        ...,
        description="Média geral das notas",
        examples=[7.2]
    )
    std_deviation: float = Field(
        ...,
        description="Desvio padrão geral",
        examples=[1.8]
    )
    max_score: float = Field(
        ...,
        description="Maior nota obtida",
        examples=[9.5]
    )
    min_score: float = Field(
        ...,
        description="Menor nota obtida",
        examples=[3.0]
    )
    median: float = Field(
        ...,
        description="Mediana das notas",
        examples=[7.5]
    )
    distribution: List[ScoreDistribution] = Field(
        default_factory=list,
        description="Distribuição de notas por faixa"
    )


class ExamResultsResponse(BaseModel):
    """Response com resultados completos de uma prova corrigida."""
    
    model_config = ConfigDict(from_attributes=True)
    
    exam_uuid: UUID = Field(
        ...,
        description="UUID da prova"
    )
    exam_title: str = Field(
        ...,
        description="Título da prova",
        examples=["Avaliação POO - 2024.1"]
    )
    status: str = Field(
        ...,
        description="Status da correção (GRADED, PARTIAL, PENDING)",
        examples=["GRADED"]
    )
    graded_at: Optional[datetime] = Field(
        default=None,
        description="Data/hora em que a correção foi concluída"
    )
    statistics: ExamStatistics = Field(
        ...,
        description="Estatísticas gerais da prova"
    )
    questions_stats: List[QuestionStatistics] = Field(
        default_factory=list,
        description="Estatísticas por questão"
    )
