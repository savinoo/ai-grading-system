import sys
import os

# Add project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import logging
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from src.domain.schemas import AgentCorrection, AgentID
from src.domain.state import GraphState
from src.config.prompts import (
    ARBITER_SYSTEM_PROMPT, 
    format_rubric_text, 
    format_rag_context
)

logger = logging.getLogger(__name__)

class ArbiterAgent:
    """
    Agente de Desempate (Corretor 3).
    Atua apenas quando há divergência significativa (> Limiar).
    Analisa o 'debate' entre C1 e C2 para emitir um veredito fundamentado.
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.structured_llm = self.llm.with_structured_output(AgentCorrection, method="function_calling")

    async def arbitrate(self, state: GraphState) -> AgentCorrection:
        """
        Executa a arbitragem:
        1. Recupera as correções de C1 e C2 do estado.
        2. Injeta o 'conflito' no prompt do Árbitro.
        3. Gera a nota de desempate.
        """
        try:
            logger.info("[ARBITER] Iniciando processo de desempate...")

            # 1. Extração dos Agentes Anteriores
            # Precisamos encontrar quem é quem na lista de correções
            c1_correction = next(c for c in state["individual_corrections"] if c.agent_id == AgentID.CORRETOR_1)
            c2_correction = next(c for c in state["individual_corrections"] if c.agent_id == AgentID.CORRETOR_2)
            
            question = state["question"]
            student_answer = state["student_answer"]
            rag_context = state["rag_context"]

            # 2. Preparação do Prompt
            # Aqui está a 'mágica' do SMA: O árbitro vê o raciocínio dos outros.
            prompt = ChatPromptTemplate.from_template(ARBITER_SYSTEM_PROMPT)
            
            chain = prompt | self.structured_llm

            # 3. Invocação
            result: AgentCorrection = await chain.ainvoke({
                # Contexto Estático
                "question_statement": question.statement,
                "rubric_formatted": format_rubric_text(question.rubric),
                "rag_context_formatted": format_rag_context(rag_context),
                "student_answer": student_answer.text,
                
                # Contexto do Conflito (Meta-Avaliação)
                "score_c1": c1_correction.total_score,
                "reasoning_c1": c1_correction.reasoning_chain,
                
                "score_c2": c2_correction.total_score,
                "reasoning_c2": c2_correction.reasoning_chain,
                
                "divergence_value": state["divergence_value"]
            })

            # Força a identidade do Árbitro
            result.agent_id = AgentID.ARBITER
            
            logger.info(f"[ARBITER] Veredito final: {result.total_score}. Feedback: {result.feedback_text[:50]}...")
            
            return result

        except StopIteration:
            logger.error("ERRO CRÍTICO: Árbitro chamado sem correções prévias de C1 e C2.")
            raise ValueError("Estado inválido para arbitragem.")
        except Exception as e:
            logger.error(f"Erro na execução do Árbitro: {str(e)}")
            raise e

# --- Exemplo de Uso (Unit Test simulado) ---
if __name__ == "__main__":
    # Este bloco só roda se executarmos o arquivo diretamente para teste manual
    import asyncio
    from langchain_openai import ChatOpenAI
    from src.config.settings import settings
    
    # Ensure environment variables are loaded
    settings.validate()

    # Mock simples
    mock_llm = ChatOpenAI(model=settings.MODEL_NAME, temperature=settings.TEMPERATURE)
    agent = ArbiterAgent(mock_llm)
    
    print("Módulo ArbiterAgent carregado com sucesso.")