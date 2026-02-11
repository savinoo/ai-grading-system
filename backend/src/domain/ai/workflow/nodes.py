from __future__ import annotations

from src.services.rag.retrieval_service import RetrievalService
from src.services.agents.examiner_agent import ExaminerAgent
from src.services.agents.arbiter_agent import ArbiterAgent
from src.domain.ai.utils.divergence_checker import DivergenceChecker
from src.domain.ai.utils.consensus_builder import ConsensusBuilder
from src.domain.ai.agent_schemas import AgentID
from src.domain.ai.workflow.state import GradingState

from src.core.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# Node 1: RAG Retrieval
# =============================================================================

async def retrieve_context_node(state: GradingState) -> dict:
    """
    Busca contexto RAG para a questão usando material didático do exame.
    
    Output: state['rag_contexts'] preenchido
    """
    logger.info(
        "[RAG Node] Buscando contexto para questão %s",
        state['question'].id
    )
    
    rag_service = RetrievalService()
    contexts = await rag_service.search_context(
        query=state['question'].statement,
        exam_uuid=state['exam_uuid'],
        discipline=state['question'].metadata.discipline,
        topic=state['question'].metadata.topic
    )
    
    logger.info("[RAG Node] Recuperados %d contextos", len(contexts))
    return {"rag_contexts": contexts}


# =============================================================================
# Node 2: Corretor 1
# =============================================================================

async def examiner_1_node(state: GradingState) -> dict:
    """
    Avaliação independente do Corretor 1.
    
    Output: state['correction_1'] preenchido
    """
    logger.info("[Corretor 1 Node] Iniciando avaliação")
    
    agent = ExaminerAgent()
    correction = await agent.evaluate(
        agent_id=AgentID.CORRETOR_1,
        question=state['question'],
        student_answer=state['student_answer'],
        rag_contexts=state['rag_contexts']
    )
    
    logger.info(
        "[Corretor 1 Node] Nota: %.2f",
        correction.total_score
    )
    # Retornar apenas o campo modificado para evitar conflito em execução paralela
    return {"correction_1": correction}


# =============================================================================
# Node 3: Corretor 2
# =============================================================================

async def examiner_2_node(state: GradingState) -> dict:
    """
    Avaliação independente do Corretor 2.
    
    Output: state['correction_2'] preenchido
    """
    logger.info("[Corretor 2 Node] Iniciando avaliação")
    
    agent = ExaminerAgent()
    correction = await agent.evaluate(
        agent_id=AgentID.CORRETOR_2,
        question=state['question'],
        student_answer=state['student_answer'],
        rag_contexts=state['rag_contexts']
    )
    
    logger.info(
        "[Corretor 2 Node] Nota: %.2f",
        correction.total_score
    )
    # Retornar apenas o campo modificado para evitar conflito em execução paralela
    return {"correction_2": correction}


# =============================================================================
# Node 4: Divergence Check
# =============================================================================

async def divergence_check_node(state: GradingState) -> dict:
    """
    Verifica se há divergência entre C1 e C2 que justifique árbitro.
    
    Output: 
        - state['divergence_detected']
        - state['divergence_value']
    """
    logger.info("[Divergence Check Node] Calculando divergência")
    
    checker = DivergenceChecker()
    result = checker.check_divergence([
        state['correction_1'],
        state['correction_2']
    ])
    
    logger.info(
        "[Divergence Check Node] Divergente: %s (diff=%.2f)",
        result['is_divergent'], result['difference']
    )
    return {
        "divergence_detected": result['is_divergent'],
        "divergence_value": result['difference']
    }


# =============================================================================
# Node 5: Árbitro (Condicional)
# =============================================================================

async def arbiter_node(state: GradingState) -> dict:
    """
    Meta-avaliação pelo árbitro para resolver divergência.
    
    IMPORTANTE: Só é chamado se divergence_detected = True
    
    Output: state['correction_arbiter'] preenchido
    """
    logger.warning(
        "[Arbitro Node] Divergência detectada (%.2f pontos). Acionando árbitro...",
        state['divergence_value']
    )
    
    agent = ArbiterAgent()
    correction = await agent.evaluate(
        question=state['question'],
        student_answer=state['student_answer'],
        rag_contexts=state['rag_contexts'],
        correction_1=state['correction_1'],
        correction_2=state['correction_2']
    )
    
    logger.info(
        "[Arbitro Node] Nota do árbitro: %.2f",
        correction.total_score
    )
    return {"correction_arbiter": correction}


# =============================================================================
# Node 6: Finalização
# =============================================================================

async def finalize_node(state: GradingState) -> dict:
    """
    Calcula consenso e finaliza correção.
    
    Combina 2 ou 3 avaliações (C1, C2, opcionalmente Árbitro) em nota final.
    
    Output:
        - state['all_corrections']
        - state['final_score']
    """
    logger.info("[Finalize Node] Calculando consenso")
    
    # Coletar todas as correções disponíveis
    corrections = [state['correction_1'], state['correction_2']]
    if state.get('correction_arbiter'):
        corrections.append(state['correction_arbiter'])
    
    # Calcular nota final via consenso
    consensus = ConsensusBuilder()
    final_score = consensus.calculate_final_score(corrections)
    
    logger.info(
        "[Finalize Node] Nota final: %.2f (baseada em %d avaliações)",
        final_score, len(corrections)
    )
    return {
        "all_corrections": corrections,
        "final_score": final_score
    }
