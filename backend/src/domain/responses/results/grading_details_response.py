"""
Response models para detalhes da correção de uma resposta.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class StudentInfo(BaseModel):
    """Informações do aluno."""
    
    uuid: UUID = Field(..., description="UUID do aluno")
    name: str = Field(..., description="Nome do aluno", examples=["João Silva"])
    email: Optional[str] = Field(None, description="Email do aluno")


class QuestionInfo(BaseModel):
    """Informações da questão."""
    
    uuid: UUID = Field(..., description="UUID da questão")
    statement: str = Field(..., description="Enunciado completo da questão")
    max_score: float = Field(..., description="Pontuação máxima", examples=[10.0])


class AgentScoreBreakdown(BaseModel):
    """Breakdown das notas de cada agente por critério."""
    
    corretor_1: Optional[float] = Field(None, description="Nota do Corretor 1")
    corretor_2: Optional[float] = Field(None, description="Nota do Corretor 2")
    arbiter: Optional[float] = Field(None, description="Nota do Árbitro")


class CriterionScoreDetail(BaseModel):
    """Score detalhado de um critério com breakdown por agente."""
    
    criterion_uuid: UUID = Field(..., description="UUID do critério")
    criterion_name: str = Field(..., description="Nome do critério", examples=["Conceito Correto"])
    max_score: float = Field(..., description="Pontuação máxima do critério", examples=[4.0])
    raw_score: float = Field(..., description="Pontuação obtida", examples=[3.5])
    weighted_score: Optional[float] = Field(None, description="Pontuação ponderada")
    feedback: Optional[str] = Field(None, description="Feedback específico do critério")
    agent_scores: AgentScoreBreakdown = Field(
        default_factory=AgentScoreBreakdown,
        description="Breakdown das notas de cada agente"
    )


class CriterionScoreSimple(BaseModel):
    """Score simplificado de critério para uso dentro de AgentCorrection."""
    
    criterion_name: str = Field(..., description="Nome do critério")
    score: float = Field(..., description="Pontuação obtida")
    max_score: float = Field(..., description="Pontuação máxima")
    feedback: Optional[str] = Field(None, description="Feedback do critério")


class AgentCorrectionDetail(BaseModel):
    """Detalhes da correção de um agente específico."""
    
    agent_id: str = Field(
        ...,
        description="ID do agente",
        examples=["corretor_1", "corretor_2", "corretor_3_arbiter"]
    )
    agent_name: str = Field(
        ...,
        description="Nome amigável do agente",
        examples=["GPT-4", "Claude", "GPT-4o"]
    )
    total_score: float = Field(..., description="Nota total atribuída", examples=[8.5])
    reasoning_chain: str = Field(
        ...,
        description="Chain-of-Thought completo do agente"
    )
    feedback_text: str = Field(..., description="Feedback do agente")
    confidence_level: Optional[float] = Field(
        None,
        description="Nível de confiança (0.0 a 1.0)",
        examples=[0.85]
    )
    criteria_scores: List[CriterionScoreSimple] = Field(
        default_factory=list,
        description="Scores por critério"
    )


class RAGContextItem(BaseModel):
    """Item de contexto recuperado pelo RAG."""
    
    content: str = Field(..., description="Conteúdo do trecho recuperado")
    source: str = Field(..., description="Fonte do trecho", examples=["aula-05-polimorfismo.pdf"])
    page: Optional[int] = Field(None, description="Página do documento", examples=[12])
    relevance_score: float = Field(..., description="Score de relevância", examples=[0.92])


class GradingDetailsResponse(BaseModel):
    """Response com detalhes completos da correção de uma resposta."""
    
    model_config = ConfigDict(from_attributes=True)
    
    answer_uuid: UUID = Field(..., description="UUID da resposta")
    student: StudentInfo = Field(..., description="Informações do aluno")
    question: QuestionInfo = Field(..., description="Informações da questão")
    answer_text: str = Field(..., description="Texto da resposta do aluno")
    
    # Resultado final
    final_score: float = Field(..., description="Nota final", examples=[9.0])
    status: str = Field(..., description="Status da correção", examples=["GRADED"])
    graded_at: Optional[datetime] = Field(None, description="Data/hora da correção")
    
    # Feedback consolidado
    final_feedback: str = Field(..., description="Feedback consolidado ao aluno")
    
    # Divergência
    divergence_detected: bool = Field(
        ...,
        description="Se houve divergência entre corretores"
    )
    divergence_value: Optional[float] = Field(
        None,
        description="Valor da divergência em pontos",
        examples=[1.5]
    )
    
    # Scores por critério (consolidado final)
    criteria_scores: List[CriterionScoreDetail] = Field(
        default_factory=list,
        description="Scores detalhados por critério"
    )
    
    # Detalhes dos agentes
    corrections: List[AgentCorrectionDetail] = Field(
        default_factory=list,
        description="Correções de cada agente"
    )
    
    # Contexto RAG
    rag_context: List[RAGContextItem] = Field(
        default_factory=list,
        description="Contexto RAG utilizado na correção"
    )
