# src/workflow/graph.py
import logging
from langgraph.graph import StateGraph, END
from src.domain.state import GraphState
from src.workflow.nodes import (
    retrieve_context_node,
    corrector_1_node,
    corrector_2_node,
    calculate_divergence_node,
    arbiter_node,
    finalize_grade_node
)

logger = logging.getLogger(__name__)

def build_grading_workflow():
    """
    Constrói o Grafo Executável do LangGraph.
    Reflete o fluxograma da Figura 3 do TCC.
    """
    workflow = StateGraph(GraphState)

    # 1. Adicionar Nós
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("corrector_1", corrector_1_node)
    workflow.add_node("corrector_2", corrector_2_node)
    workflow.add_node("check_divergence", calculate_divergence_node)
    workflow.add_node("arbiter", arbiter_node)
    workflow.add_node("finalize", finalize_grade_node)

    # 2. Definir Arestas (O Fluxo)
    
    # Início -> RAG
    workflow.set_entry_point("retrieve_context")
    
    # RAG -> Paralelismo (C1 e C2 rodam ao mesmo tempo)
    workflow.add_edge("retrieve_context", "corrector_1")
    workflow.add_edge("retrieve_context", "corrector_2")
    
    # Sincronização: Ambos devem terminar antes de checar divergência
    workflow.add_edge("corrector_1", "check_divergence")
    workflow.add_edge("corrector_2", "check_divergence")
    
    # 3. Aresta Condicional (O "Cérebro" do fluxo)
    # Decide se chama o Árbitro ou finaliza
    def router(state: GraphState):
        if state["divergence_detected"]:
            logger.info("Fluxo: Divergência detectada -> Roteando para ARBITER (Caminho da Divergência)")
            return "arbiter" # Caminho da divergência
        else:
            logger.info("Fluxo: Consenso -> Roteando para FINALIZE (Caminho Feliz)")
            return "finalize" # Caminho feliz
            
    workflow.add_conditional_edges(
        "check_divergence",
        router,
        {
            "arbiter": "arbiter",
            "finalize": "finalize"
        }
    )
    
    # Árbitro -> Finalizar
    workflow.add_edge("arbiter", "finalize")
    
    # Finalizar -> Fim
    workflow.add_edge("finalize", END)

    # Compila o grafo
    return workflow.compile()