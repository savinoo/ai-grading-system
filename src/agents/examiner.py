import sys
import os


import logging
import openai
from typing import Any
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from src.domain.schemas import AgentCorrection, AgentID
from src.domain.state import GraphState
from src.config.settings import settings
from src.config.prompts import (
    CORRECTOR_SYSTEM_PROMPT, 
    format_rubric_text, 
    format_rag_context
)


# Configuração de Logs para observabilidade
logger = logging.getLogger(__name__)

class ExaminerAgent:
    """
    Agente responsável pela correção individual (Corretor 1 e Corretor 2).
    Este componente é agnóstico ao modelo (pode usar GPT-4, Claude, Llama),
    desde que o modelo suporte output estruturado.
    """

    def __init__(self, llm: BaseChatModel):
        """
        Injeção de dependência do LLM para facilitar testes e troca de modelos.
        """
        self.llm = llm
        # Prepara o modelo para forçar a saída no schema AgentCorrection
        self.structured_llm = self.llm.with_structured_output(AgentCorrection, method="function_calling")

    @traceable(run_type="chain", name="Examiner Agent Evaluation")
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.INITIAL_RETRY_DELAY, max=settings.MAX_RETRY_DELAY),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError)),
        reraise=True
    )
    async def evaluate(self, state: GraphState, agent_id: AgentID) -> AgentCorrection:
        """
        Executa o pipeline de avaliação:
        1. Prepara os dados do State.
        2. Formata o Prompt com Contexto RAG e Rubrica.
        3. Invoca o LLM.
        4. Retorna o objeto validado.
        """
        try:
            # 1. Extração de dados do Estado
            question = state["question"]
            student_answer = state["student_answer"]
            rag_context = state["rag_context"]

            # 2. Formatação dos Inputs para o Prompt
            formatted_rubric = format_rubric_text(question.rubric)
            formatted_context = format_rag_context(rag_context)

            # 3. Construção do Template de Chat
            # Usamos ChatPromptTemplate para separar System de Human (se necessário)
            # Aqui, como o prompt é denso, passamos tudo como System/Instruction
            prompt = ChatPromptTemplate.from_template(CORRECTOR_SYSTEM_PROMPT)
            
            chain = prompt | self.structured_llm

            logger.info(f"[{agent_id}] Iniciando avaliação da questão {question.id}...")

            # 4. Invocação (Assíncrona para paralelismo no LangGraph)
            result: AgentCorrection = await chain.ainvoke({
                "question_statement": question.statement,
                "rubric_formatted": formatted_rubric,
                "rag_context_formatted": formatted_context,
                "student_answer": student_answer.text,
                "agent_id": agent_id.value
            })

            # Override de segurança: Garante que o ID no JSON bate com o argumento
            # Isso evita que o LLM alucine o ID errado (ex: C1 dizer que é C2)
            result.agent_id = agent_id
            
            logger.info(f"[{agent_id}] Avaliação concluída. Nota: {result.total_score}")
            
            return result

        except Exception as e:
            logger.error(f"Erro fatal no agente {agent_id}: {str(e)}")
            # Em produção, aqui implementaríamos uma lógica de Retry ou Fallback.
            # Para o TCC, lançamos o erro para ser capturado pelo Grafo.
            raise e

# --- Exemplo de Uso (Unit Test simulado) ---
if __name__ == "__main__":
    # Este bloco só roda se executarmos o arquivo diretamente para teste manual
    import asyncio
    from langchain_openai import ChatOpenAI
    from src.config.settings import settings


    # Mock simples
    mock_llm = ChatOpenAI(model=settings.MODEL_NAME, temperature=settings.TEMPERATURE) # Baixa temperatura para determinismo
    agent = ExaminerAgent(mock_llm)
    
    # O state teria que ser mockado aqui para testar
    print("Módulo ExaminerAgent carregado com sucesso.")