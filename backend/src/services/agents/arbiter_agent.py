from __future__ import annotations

from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

from src.interfaces.services.agents.arbiter_agent_interface import ArbiterAgentInterface
from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.rag_schemas import RetrievedContext
from src.domain.ai.agent_schemas import AgentCorrection, AgentID
from src.domain.ai.prompts import ARBITER_SYSTEM_PROMPT, format_rubric_text, format_rag_context
from src.core.llm_handler import get_chat_model
from src.core.settings import settings
from src.core.logging_config import get_logger

# NOTE: DSPy removido do runtime — ver examiner_agent.py para justificativa arquitetural.


class ArbiterAgent(ArbiterAgentInterface):
    """
    Agente Árbitro (C3) — ativa somente quando |C1 - C2| > DIVERGENCE_THRESHOLD.

    Usa LangChain with_structured_output(AgentCorrection): 1 chamada LLM, parse direto.
    """

    def __init__(self) -> None:
        self.__llm = get_chat_model().with_structured_output(AgentCorrection)
        self.__prompt = ChatPromptTemplate.from_messages([
            ("human", ARBITER_SYSTEM_PROMPT)
        ])
        self.__chain = self.__prompt | self.__llm
        self.__logger = get_logger(__name__)

    @traceable(run_type="chain", name="Arbiter Agent Decision")
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    async def evaluate(
        self,
        question: ExamQuestion,
        student_answer: StudentAnswer,
        rag_contexts: List[RetrievedContext],
        correction_1: AgentCorrection,
        correction_2: AgentCorrection
    ) -> AgentCorrection:
        """
        Executa arbitragem entre duas avaliações divergentes.

        Args:
            question: Questão com enunciado e rubrica
            student_answer: Resposta discursiva do aluno
            rag_contexts: Contextos recuperados via RAG
            correction_1: Avaliação do CORRETOR_1
            correction_2: Avaliação do CORRETOR_2

        Returns:
            AgentCorrection: Resultado estruturado da arbitração
        """
        divergence = abs(correction_1.total_score - correction_2.total_score)
        self.__logger.info(
            "[ARBITER] Iniciando arbitragem para questão %s (divergência: %.2f pontos)",
            question.id, divergence
        )

        result: AgentCorrection = await self.__chain.ainvoke({
            "question_statement": question.statement,
            "rubric_formatted": format_rubric_text(question.rubric),
            "rag_context_formatted": format_rag_context(rag_contexts),
            "student_answer": student_answer.text,
            "score_c1": correction_1.total_score,
            "score_c2": correction_2.total_score,
            "divergence_value": round(divergence, 2),
            "reasoning_c1": correction_1.reasoning_chain,
            "reasoning_c2": correction_2.reasoning_chain,
        })

        result.agent_id = AgentID.ARBITER

        self.__logger.info(
            "[ARBITER] Arbitragem concluída. Nota final: %.2f (C1=%.2f | C2=%.2f)",
            result.total_score, correction_1.total_score, correction_2.total_score
        )
        return result
