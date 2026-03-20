"""
Response models para revisão de provas corrigidas.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class CriterionScore(BaseModel):
    """Score de um critério específico."""
    
    criterion_uuid: UUID = Field(..., description="UUID do critério")
    criterion_name: str = Field(..., description="Nome do critério", examples=["Conceito Correto"])
    criterion_description: Optional[str] = Field(None, description="Descrição do critério")
    max_score: float = Field(..., description="Pontuação máxima", examples=[4.0])
    weight: float = Field(..., description="Peso do critério", examples=[0.4])
    raw_score: float = Field(..., description="Pontuação obtida", examples=[3.5])
    weighted_score: Optional[float] = Field(None, description="Pontuação ponderada")
    feedback: Optional[str] = Field(None, description="Feedback específico do critério")

class StudentAnswerReview(BaseModel):
    """Resposta de um aluno para revisão."""
    
    answer_uuid: UUID = Field(..., description="UUID da resposta")
    student_uuid: UUID = Field(..., description="UUID do aluno")
    student_name: str = Field(..., description="Nome do aluno", examples=["João Silva"])
    student_email: Optional[str] = Field(None, description="Email do aluno")
    
    answer_text: str = Field(..., description="Texto da resposta do aluno")
    score: Optional[float] = Field(None, description="Nota final", examples=[8.5])
    status: str = Field(..., description="Status da correção", examples=["GRADED"])
    feedback: Optional[str] = Field(None, description="Feedback consolidado")
    
    criteria_scores: List[CriterionScore] = Field(
        default_factory=list,
        description="Scores por critério"
    )
        
    graded_at: Optional[datetime] = Field(None, description="Data/hora da correção")


class QuestionReview(BaseModel):
    """Questão com todas as respostas dos alunos."""
    
    question_uuid: UUID = Field(..., description="UUID da questão")
    question_number: int = Field(..., description="Número da questão", examples=[1])
    statement: str = Field(..., description="Enunciado da questão")
    expected_answer: Optional[str] = Field(None, description="Resposta esperada/gabarito")
    max_score: float = Field(..., description="Pontuação máxima", examples=[10.0])
    
    student_answers: List[StudentAnswerReview] = Field(
        default_factory=list,
        description="Respostas dos alunos"
    )


class ExamReviewResponse(BaseModel):
    """Response completa para revisão de uma prova."""
    
    model_config = ConfigDict(from_attributes=True)
    
    exam_uuid: UUID = Field(..., description="UUID da prova")
    exam_title: str = Field(..., description="Título da prova", examples=["Prova Final - POO"])
    exam_description: Optional[str] = Field(None, description="Descrição da prova")
    
    class_name: Optional[str] = Field(None, description="Nome da turma")
    status: str = Field(..., description="Status da prova", examples=["GRADED"])
    
    total_students: int = Field(..., description="Total de alunos", examples=[25])
    total_questions: int = Field(..., description="Total de questões", examples=[5])
    
    graded_at: Optional[datetime] = Field(None, description="Data da correção")
    
    questions: List[QuestionReview] = Field(
        default_factory=list,
        description="Questões com respostas dos alunos"
    )
    
    # Critérios da prova (globais)
    grading_criteria: List[CriterionScore] = Field(
        default_factory=list,
        description="Critérios de avaliação configurados na prova"
    )
