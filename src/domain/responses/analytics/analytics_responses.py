"""
Schemas de resposta para o módulo de análise pedagógica.
"""
from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class LearningGapResponse(BaseModel):
    """Fraqueza identificada em critérios de avaliação."""

    criterion_name: str
    severity: Literal["low", "medium", "high"]
    evidence_count: int
    avg_score: float
    suggestion: Optional[str] = None


class StrengthResponse(BaseModel):
    """Ponto forte consistente do aluno."""

    criterion_name: str
    avg_score: float
    consistency: float = Field(..., description="0-1, consistência com que o aluno se destaca neste critério")


class SubmissionSummaryResponse(BaseModel):
    """Resumo de uma submissão corrigida na linha do tempo do aluno."""

    answer_uuid: UUID
    question_uuid: UUID
    exam_uuid: UUID
    exam_title: str
    score: float
    max_score: float
    graded_at: Optional[datetime] = None


class StudentPerformanceResponse(BaseModel):
    """
    Perfil analítico completo de um estudante.
    Alimenta a visão de desempenho individual do professor.
    """

    student_uuid: UUID
    student_name: str
    student_email: Optional[str] = None

    # Métricas gerais
    avg_score: float = 0.0
    submission_count: int = 0
    trend: Literal["improving", "stable", "declining", "insufficient_data"] = "insufficient_data"
    trend_confidence: float = 0.0

    # Padrões detectados
    learning_gaps: List[LearningGapResponse] = Field(default_factory=list)
    strengths: List[StrengthResponse] = Field(default_factory=list)

    # Histórico
    submissions_history: List[SubmissionSummaryResponse] = Field(default_factory=list)

    # Metadados
    first_submission: Optional[datetime] = None
    last_submission: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class GradeDistributionResponse(BaseModel):
    """Distribuição de notas por faixas de desempenho."""

    label: str = Field(..., description="Ex: A, B, C, D, F")
    range: str = Field(..., description="Ex: 9-10, 7-9, 5-7, 3-5, 0-3")
    count: int
    percentage: float


class ClassStudentSummaryResponse(BaseModel):
    """Resumo de um aluno dentro do contexto da turma."""

    student_uuid: UUID
    student_name: str
    avg_score: float
    submission_count: int
    trend: Literal["improving", "stable", "declining", "insufficient_data"] = "insufficient_data"


class ClassAnalyticsResponse(BaseModel):
    """
    Análise pedagógica agregada de uma turma.
    Alimenta o painel analítico do professor sobre a turma.
    """

    class_uuid: UUID
    class_name: str

    # Quantidade
    total_students: int
    total_submissions: int

    # Métricas da turma
    class_avg_score: float
    median_score: float
    std_deviation: float

    # Distribuição de notas (A/B/C/D/F)
    grade_distribution: List[GradeDistributionResponse] = Field(default_factory=list)

    # Outliers pedagógicos
    struggling_students: List[ClassStudentSummaryResponse] = Field(
        default_factory=list,
        description="Alunos com média > 1 desvio padrão abaixo da média da turma"
    )
    top_performers: List[ClassStudentSummaryResponse] = Field(
        default_factory=list,
        description="Alunos com média > 1 desvio padrão acima da média da turma"
    )

    # Gaps mais comuns na turma
    most_common_gaps: List[LearningGapResponse] = Field(default_factory=list)

    # Perfis individuais
    students: List[ClassStudentSummaryResponse] = Field(default_factory=list)

    analysis_timestamp: datetime = Field(default_factory=datetime.now)


class ClassAnalyticsSummaryResponse(BaseModel):
    """
    Resumo analítico de uma turma para listagem (sem detalhe por aluno).
    """

    class_uuid: UUID
    class_name: str
    total_students: int
    total_submissions: int
    class_avg_score: float
    struggling_count: int
    top_performers_count: int
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
