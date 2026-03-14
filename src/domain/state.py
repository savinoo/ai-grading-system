# src/domain/state.py
import operator
from typing import Annotated, TypedDict

from src.domain.schemas import AgentCorrection, ExamQuestion, RetrievedContext, StudentAnswer


class GraphState(TypedDict):
    """
    O Estado Partilhado do LangGraph.
    Armazena todo o contexto da execução atual de uma correção.
    """

    # --- Inputs (Dados de Entrada) ---
    question: ExamQuestion
    student_answer: StudentAnswer

    # --- RAG Data (Contexto) ---
    # Lista de chunks recuperados do Vector DB que fundamentam a correção
    rag_context: list[RetrievedContext]

    # --- Agent Outputs (Resultados Intermédios) ---
    # Armazena as correções individuais.
    # Usamos uma lista para permitir que C1 e C2 escrevam em paralelo sem race conditions complexas.
    individual_corrections: Annotated[list[AgentCorrection], operator.add]

    # --- Control Flow (Controlo de Fluxo) ---
    # Flag calculada para decidir se chamamos o Corretor 3 [cite: 752]
    divergence_detected: bool
    divergence_value: float # O valor absoluto da diferença entre C1 e C2

    # --- Final Output (Resultado Final) ---
    final_grade: float | None
    final_feedback_summary: str | None
    processing_metadata: dict # Para auditoria (ex: tempo de execução, tokens gastos)
