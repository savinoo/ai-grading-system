"""
Definição do grafo LangGraph para correção automática.
Orquestra fluxo: RAG → C1+C2 (paralelo) → Divergence → Árbitro → Finalização.
"""

import logging
from langgraph.graph import StateGraph, END
from .state import GradingState
from .nodes import (
    retrieve_context_node,
    examiner_1_node,
    examiner_2_node,
    divergence_check_node,
    arbiter_node,
    finalize_node
)

logger = logging.getLogger(__name__)


def should_call_arbiter(state: GradingState) -> str:
    """
    Roteamento condicional: divergente → arbiter, caso contrário → finalize.
    
    Args:
        state: Estado atual do grafo
    
    Returns:
        "arbiter" se divergência detectada, "finalize" caso contrário
    """
    if state.get('divergence_detected', False):
        logger.info("[Router] Roteando para ARBITER (divergência detectada)")
        return "arbiter"
    else:
        logger.info("[Router] Roteando para FINALIZE (sem divergência)")
        return "finalize"


def create_grading_graph() -> StateGraph:
    """
    Cria o grafo de correção com LangGraph.
    
    Estrutura do grafo:
    ```
    START
      ↓
    retrieve_context
      ↓
      ├─→ examiner_1 ─┐
      └─→ examiner_2 ─┤ (paralelo)
                      ↓
              divergence_check
                      ↓
             [condicional routing]
                      ↓
            ┌─────────┴─────────┐
            ↓                   ↓
         arbiter            finalize
            ↓                   ↑
            └───────────────────┘
                      ↓
                     END
    ```
    
    Returns:
        Grafo compilado pronto para execução
    """
    
    workflow = StateGraph(GradingState)
    
    # === Adicionar Nodes ===
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("examiner_1", examiner_1_node)
    workflow.add_node("examiner_2", examiner_2_node)
    workflow.add_node("divergence_check", divergence_check_node)
    workflow.add_node("arbiter", arbiter_node)
    workflow.add_node("finalize", finalize_node)
    
    # === Definir Entry Point ===
    workflow.set_entry_point("retrieve_context")
    
    # === Edges (Fluxo Linear até divergência) ===
    # RAG → Corretores (paralelo)
    workflow.add_edge("retrieve_context", "examiner_1")
    workflow.add_edge("retrieve_context", "examiner_2")
    
    # Corretores → Divergência
    workflow.add_edge("examiner_1", "divergence_check")
    workflow.add_edge("examiner_2", "divergence_check")
    
    # === Conditional Edge (Divergência) ===
    workflow.add_conditional_edges(
        "divergence_check",
        should_call_arbiter,
        {
            "arbiter": "arbiter",
            "finalize": "finalize"
        }
    )
    
    # === Edges para finalização ===
    workflow.add_edge("arbiter", "finalize")
    workflow.add_edge("finalize", END)
    
    logger.info("Grafo de correção criado com sucesso")
    return workflow.compile()


# =============================================================================
# Singleton Global
# =============================================================================

_grading_graph = None


def get_grading_graph() -> StateGraph:
    """
    Retorna instância compilada do grafo (singleton pattern).
    
    Evita recompilação desnecessária em cada chamada.
    
    Returns:
        Grafo compilado pronto para uso
    """
    global _grading_graph  # pylint: disable=global-statement
    if _grading_graph is None:
        logger.info("Compilando grafo de correção pela primeira vez")
        _grading_graph = create_grading_graph()
    return _grading_graph
