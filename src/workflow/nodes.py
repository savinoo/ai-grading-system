# src/workflow/nodes.py
import logging
from typing import Any

from src.agents.dspy_arbiter import DSPyArbiterAgent
from src.agents.dspy_examiner import DSPyExaminerAgent
from src.config.settings import settings
from src.domain.schemas import AgentID
from src.domain.state import GraphState
from src.rag.retriever import search_context
from src.utils.helpers import measure_time

logger = logging.getLogger(__name__)

# Lazy initialization: agents are created on first use, not at import time.
# Avoids LLM client creation when module is imported by test runners or Streamlit
# before the environment (keys, event loop) is ready.
_examiner: DSPyExaminerAgent | None = None
_arbiter: DSPyArbiterAgent | None = None

def _get_examiner() -> DSPyExaminerAgent:
    global _examiner
    if _examiner is None:
        _examiner = DSPyExaminerAgent()
    return _examiner

def _get_arbiter() -> DSPyArbiterAgent:
    global _arbiter
    if _arbiter is None:
        _arbiter = DSPyArbiterAgent()
    return _arbiter


async def retrieve_context_node(state: GraphState) -> dict[str, Any]:
    """
    Nó de RAG: Recupera contexto do Vector DB com filtragem.
    """
    with measure_time("Nó RAG (Retrieve Context)"):
        # OTIMIZAÇÃO: Se o contexto já foi injetado (no modo batch otimizado), usa ele e não busca de novo.
        if state.get("rag_context") and len(state["rag_context"]) > 0:
            logger.info("--- RAG: CONTEXTO PRÉ-CARREGADO (CACHE) ---")
            return {"rag_context": state["rag_context"]}

        logger.info("--- RAG: RECUPERANDO CONTEXTO ---")

        question = state["question"]

        # Busca usando os metadados da questão para filtrar (EU-COR01)
        context_results = search_context(
            query=question.statement, # Buscamos contexto para entender a QUESTAO
            discipline=question.metadata.discipline,
            topic=question.metadata.topic
        )

        logger.info(f"Contextos recuperados: {len(context_results)}")

        return {"rag_context": context_results}

async def corrector_1_node(state: GraphState) -> dict[str, Any]:
    """Executa o Corretor 1"""
    with measure_time("Nó Corretor 1"):
        logger.info("--- AGENTE: CORRETOR 1 ---")
        result = await _get_examiner().evaluate(state, agent_id=AgentID.CORRETOR_1)
        return {"individual_corrections": [result]}

async def corrector_2_node(state: GraphState) -> dict[str, Any]:
    """Executa o Corretor 2"""
    with measure_time("Nó Corretor 2"):
        logger.info("--- AGENTE: CORRETOR 2 ---")
        result = await _get_examiner().evaluate(state, agent_id=AgentID.CORRETOR_2)
        return {"individual_corrections": [result]}

def calculate_divergence_node(state: GraphState) -> dict[str, Any]:
    """
    Nó Lógico: Verifica se há divergência entre C1 e C2.
    Implementa a lógica da seção 4.2.3.4 do TCC.
    """
    logger.info("--- CÁLCULO DE DIVERGÊNCIA ---")
    corrections = state["individual_corrections"]

    c1 = next((c for c in corrections if c.agent_id == AgentID.CORRETOR_1), None)
    c2 = next((c for c in corrections if c.agent_id == AgentID.CORRETOR_2), None)
    if c1 is None or c2 is None:
        raise ValueError(f"Correções incompletas: C1={c1}, C2={c2}. Estado: {[c.agent_id for c in corrections]}")

    diff = abs(c1.total_score - c2.total_score)
    # Lê do estado do grafo se passado (evita mutar singleton global)
    # Fallback para settings default se não fornecido
    threshold = state.get("divergence_threshold") or settings.DIVERGENCE_THRESHOLD

    is_divergent = diff > threshold

    logger.info(f"Diferença: {diff:.2f} | Limiar: {threshold} | Divergente? {is_divergent}")

    return {
        "divergence_detected": is_divergent,
        "divergence_value": diff
    }

async def arbiter_node(state: GraphState) -> dict[str, Any]:
    """Executa o Corretor 3 (Árbitro) se necessário"""
    with measure_time("Nó Árbitro (C3)"):
        logger.info("--- AGENTE: ÁRBITRO (C3) ---")
        result = await _get_arbiter().arbitrate(state)
        return {"individual_corrections": [result]}

def finalize_grade_node(state: GraphState) -> dict[str, Any]:
    """
    Algoritmo de Consenso (Seção 4.2.3.6).
    Calcula a nota final baseada na média ou nas notas mais próximas.
    """
    logger.info("--- FINALIZANDO NOTA ---")
    corrections = state["individual_corrections"]

    # Extrai todas as notas
    scores = [c.total_score for c in corrections]

    final_score = 0.0

    if len(scores) == 2:
        # Caso sem divergência: média simples de C1 e C2
        final_score = sum(scores) / 2
        logger.info(f"Consenso simples (C1+C2)/2: {final_score}")

    elif len(scores) == 3:
        # Caso com árbitro (C3): média aritmética dos 2 escores mais próximos entre os 3.
        # Lógica: o árbitro serve como "desempate por aproximação" — a nota final
        # é a média do par com menor distância absoluta.
        # Exemplo: [3.0, 7.0, 8.0] → par (7,8) dist=1 < par (3,7) dist=4 → final=7.5
        scores_sorted = sorted(scores)
        diff_low  = scores_sorted[1] - scores_sorted[0]
        diff_high = scores_sorted[2] - scores_sorted[1]

        if diff_low < diff_high:
            final_score = (scores_sorted[0] + scores_sorted[1]) / 2
        else:
            final_score = (scores_sorted[1] + scores_sorted[2]) / 2

        logger.info(f"Consenso via par mais próximo: {final_score} (scores={scores_sorted})")

    return {
        "final_grade": final_score,
        # Poderíamos gerar um sumário do feedback aqui também
    }
