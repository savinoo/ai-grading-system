from __future__ import annotations

from typing import TypedDict, List, Optional
from uuid import UUID

from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.rag_schemas import RetrievedContext
from src.domain.ai.agent_schemas import AgentCorrection


class GradingState(TypedDict):
    """
    Estado compartilhado entre nodes do LangGraph de correção.
    
    Fluxo de dados:
    1. Inputs iniciais (exam_uuid, question, student_answer)
    2. RAG → rag_contexts
    3. Corretores → correction_1, correction_2
    4. Divergence → divergence_detected, divergence_value
    5. Árbitro (condicional) → correction_arbiter
    6. Finalização → all_corrections, final_score
    """
    
    # === Inputs (fornecidos externamente) ===
    exam_uuid: UUID
    question: ExamQuestion
    student_answer: StudentAnswer
    
    # === Estado intermediário ===
    rag_contexts: Optional[List[RetrievedContext]]
    correction_1: Optional[AgentCorrection]
    correction_2: Optional[AgentCorrection]
    correction_arbiter: Optional[AgentCorrection]
    
    # === Flags de controle ===
    divergence_detected: bool
    divergence_value: Optional[float]
    
    # === Output final ===
    all_corrections: List[AgentCorrection]
    final_score: Optional[float]
    error: Optional[str]
