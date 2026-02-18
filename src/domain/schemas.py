# src/domain/schemas.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum

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

class AgentCorrection(BaseModel):
    """Saída de um único agente corretor (Output Cognitivo)"""
    agent_id: AgentID
    # Forçamos o modelo a gerar o raciocínio ANTES da nota para garantir CoT
    reasoning_chain: str = Field(..., description="Chain-of-Thought (CoT): OBRIGATÓRIO. O passo-a-passo detalhado do raciocínio antes de dar a nota.")
    total_score: Optional[float] = None
    feedback_text: str = Field(default="Feedback não gerado.", description="Feedback pedagógico para o aluno")
    criteria_scores: Dict[str, float] = Field(default_factory=dict, description="Notas quebradas por critério")
    
    @model_validator(mode='after')
    def calculate_total_if_missing(self):
        # Sempre recalcula o total baseado nas parciais para evitar erros de cálculo do LLM
        if self.criteria_scores:
            self.total_score = sum(self.criteria_scores.values())
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