# src/domain/schemas.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AgentID(str, Enum):
    """Identificadores únicos para os agentes do sistema"""
    CORRETOR_1 = "corretor_1"
    CORRETOR_2 = "corretor_2"
    ARBITER = "corretor_3_arbiter"

class EvaluationCriterion(BaseModel):
    """Define um critério específico da rubrica de avaliação"""
    name: str = Field(..., description="Nome do critério (ex: Precisão Conceitual)")
    description: str = Field(..., description="Descrição do que é esperado")
    weight: float = Field(1.0, description="Peso deste critério na nota final")
    max_score: float = Field(10.0, description="Nota máxima possível para este critério")

class QuestionMetadata(BaseModel):
    """Metadados para filtragem avançada no RAG"""
    discipline: str = Field(..., description="Disciplina (ex: Estrutura de Dados)")
    topic: str = Field(..., description="Tópico específico (ex: Árvores Binárias)")
    difficulty_level: Optional[str] = None

class ExamQuestion(BaseModel):
    """Estrutura da questão da prova"""
    id: str
    statement: str = Field(..., description="O enunciado da questão")
    rubric: List[EvaluationCriterion] = Field(..., description="Critérios de avaliação definidos pelo professor")
    metadata: QuestionMetadata

class StudentAnswer(BaseModel):
    """Input: Resposta do aluno estruturada"""
    student_id: str
    question_id: str
    text: str = Field(..., description="A resposta discursiva do aluno")

class RetrievedContext(BaseModel):
    """Contexto recuperado via RAG (Chunk + Metadados)"""
    content: str
    source_document: str
    page_number: Optional[int] = None
    relevance_score: float = Field(..., description="Score de similaridade do vector DB")

class CriterionScore(BaseModel):
    """Score per criterion (more LLM-friendly than a dict)."""

    criterion: str
    score: float
    feedback: Optional[str] = None


class AgentCorrection(BaseModel):
    """Saída de um único agente corretor (Output Cognitivo)"""

    # Some model outputs omit agent_id; we inject it at runtime in the agent.
    agent_id: Optional[AgentID] = None

    # LLMs often return a list of steps; normalize to a single string.
    reasoning_chain: str = Field(
        ..., description="Chain-of-Thought (CoT): OBRIGATÓRIO. O passo-a-passo detalhado do raciocínio antes de dar a nota."
    )

    total_score: Optional[float] = None
    feedback_text: str = Field(default="Feedback não gerado.", description="Feedback pedagógico para o aluno")

    # Accept either a dict (legacy) or a list of criterion objects (preferred)
    criteria_scores: List[CriterionScore] = Field(default_factory=list, description="Notas quebradas por critério")

    @field_validator("reasoning_chain", mode="before")
    @classmethod
    def normalize_reasoning_chain(cls, v):
        if isinstance(v, list):
            return "\n".join(str(x) for x in v)
        return v

    @field_validator("criteria_scores", mode="before")
    @classmethod
    def normalize_criteria_scores(cls, v):
        # Legacy format: {"Crit": 2.0, ...}
        if isinstance(v, dict):
            return [{"criterion": k, "score": float(val)} for k, val in v.items()]
        return v

    @model_validator(mode="after")
    def calculate_total_if_missing(self):
        # Always recompute total based on per-criterion scores to avoid LLM math errors.
        if self.criteria_scores:
            # Detecta se o LLM retornou notas normalizadas (0-1) em vez de absolutas (0-10)
            # Heurística: se TODAS as notas são <= 1.5, provavelmente está normalizado
            all_scores = [cs.score for cs in self.criteria_scores]
            if all_scores and all(score <= 1.5 for score in all_scores):
                # Assume que deveria ser escala 0-10 e multiplica por 10
                logger.warning(
                    f"[NORMALIZAÇÃO] Detectadas notas normalizadas (0-1): {all_scores}. "
                    f"Convertendo para escala 0-10 (multiplicando por 10)."
                )
                for cs in self.criteria_scores:
                    cs.score = cs.score * 10.0
            
            self.total_score = float(sum(cs.score for cs in self.criteria_scores))
        elif self.total_score is None:
            self.total_score = 0.0
        return self

    @field_validator('total_score')
    @classmethod
    def check_score_range(cls, v):
        # Validação defensiva: Corrige alucinações de escala (ex: 18/20 viram 10/10)
        if v is None: return v
        if v < 0: return 0.0
        if v > 10: return 10.0
        return v