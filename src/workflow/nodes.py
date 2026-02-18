# src/workflow/nodes.py
import logging
from typing import Dict, Any
# [MODIFICADO] Usando DSPy para o Agente Examinador (Corretores 1 e 2)
# from langchain_openai import ChatOpenAI # REMOVIDO: Agora usamos factory

from src.domain.state import GraphState
from src.domain.schemas import AgentID
from src.agents.examiner import ExaminerAgent
from src.agents.dspy_examiner import DSPyExaminerAgent
from src.agents.arbiter import ArbiterAgent
from src.agents.dspy_arbiter import DSPyArbiterAgent
from src.config.settings import settings
from src.utils.helpers import measure_time
from src.infrastructure.llm_factory import get_chat_model

logger = logging.getLogger(__name__)

# Instanciação dos Agentes (Em produção, usaria Injeção de Dependência)
# Factory decide se usa GPT ou Gemini baseado no .env
llm = get_chat_model(temperature=0)

# [MODIFICADO] Usando DSPy para o Agente Examinador (Corretores 1 e 2)
examiner = DSPyExaminerAgent()
# examiner = ExaminerAgent(llm) # Versão anterior (LangChain)

# [MODIFICADO] Usando DSPy para o Agente Árbitro
arbiter = DSPyArbiterAgent()
# arbiter = ArbiterAgent(llm) # Versão anterior

from src.rag.retriever import search_context # Importar a nova função

async def retrieve_context_node(state: GraphState) -> Dict[str, Any]:
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

async def corrector_1_node(state: GraphState) -> Dict[str, Any]:
    """Executa o Corretor 1"""
    with measure_time("Nó Corretor 1"):
        logger.info("--- AGENTE: CORRETOR 1 ---")
        result = await examiner.evaluate(state, agent_id=AgentID.CORRETOR_1)
        return {"individual_corrections": [result]}

async def corrector_2_node(state: GraphState) -> Dict[str, Any]:
    """Executa o Corretor 2"""
    with measure_time("Nó Corretor 2"):
        logger.info("--- AGENTE: CORRETOR 2 ---")
        result = await examiner.evaluate(state, agent_id=AgentID.CORRETOR_2)
        return {"individual_corrections": [result]}

def calculate_divergence_node(state: GraphState) -> Dict[str, Any]:
    """
    Nó Lógico: Verifica se há divergência entre C1 e C2.
    Implementa a lógica da seção 4.2.3.4 do TCC.
    """
    logger.info("--- CÁLCULO DE DIVERGÊNCIA ---")
    corrections = state["individual_corrections"]
    
    # Busca segura das notas
    c1 = next(c for c in corrections if c.agent_id == AgentID.CORRETOR_1)
    c2 = next(c for c in corrections if c.agent_id == AgentID.CORRETOR_2)
    
    diff = abs(c1.total_score - c2.total_score)
    # Limiar configurável (ex: 1.5 pontos em escala de 0-10)
    threshold = settings.DIVERGENCE_THRESHOLD 
    
    is_divergent = diff > threshold
    
    logger.info(f"Diferença: {diff:.2f} | Limiar: {threshold} | Divergente? {is_divergent}")
    
    return {
        "divergence_detected": is_divergent,
        "divergence_value": diff
    }

async def arbiter_node(state: GraphState) -> Dict[str, Any]:
    """Executa o Corretor 3 (Árbitro) se necessário"""
    with measure_time("Nó Árbitro (C3)"):
        logger.info("--- AGENTE: ÁRBITRO (C3) ---")
        result = await arbiter.arbitrate(state)
        return {"individual_corrections": [result]}

def finalize_grade_node(state: GraphState) -> Dict[str, Any]:
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
        # Caso sem divergência: Média simples de C1 e C2
        final_score = sum(scores) / 2
        logger.info(f"Consenso Simples (C1+C2)/2: {final_score}")
        
    elif len(scores) == 3:
        # Caso com divergência: Média dos dois mais próximos
        # Lógica: Ordenar as notas e ver quais pares têm menor distância
        scores.sort() # Ex: [3.0, 7.0, 8.0]
        
        diff_low = scores[1] - scores[0]  # Distância entre menor e meio
        diff_high = scores[2] - scores[1] # Distância entre meio e maior
        
        if diff_low < diff_high:
            # Os dois menores estão mais próximos
            final_score = (scores[0] + scores[1]) / 2
        else:
            # Os dois maiores estão mais próximos (ou equidistantes)
            final_score = (scores[1] + scores[2]) / 2
            
        logger.info(f"Consenso Avançado (Pares Próximos): {final_score} a partir de {scores}")
        
    return {
        "final_grade": final_score,
        # Poderíamos gerar um sumário do feedback aqui também
    }