from __future__ import annotations

from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

from src.interfaces.services.agents.examiner_agent_interface import ExaminerAgentInterface
from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.rag_schemas import RetrievedContext
from src.domain.ai.agent_schemas import AgentCorrection, AgentID
from src.domain.ai.prompts import CORRECTOR_SYSTEM_PROMPT, format_rubric_text, format_rag_context
from src.core.llm_handler import get_chat_model
from src.core.settings import settings
from src.core.logging_config import get_logger

# NOTE: DSPy removido do runtime — DSPy é framework de OTIMIZAÇÃO de prompts (offline),
# não de inferência. Usar dspy.ChainOfThought a cada correção adicionava 1-3 chamadas
# extras desnecessárias ao LLM.
# Arquitetura correta:
#   - Offline: DSPy BootstrapFewShot otimiza o prompt com exemplos reais
#   - Runtime: LangChain with_structured_output → 1 chamada garantida, parse direto Pydantic


class ExaminerAgent(ExaminerAgentInterface):
    """
    Agente Corretor Independente (C1 ou C2).

    Usa LangChain with_structured_output(AgentCorrection) para inferência runtime:
    1 chamada LLM por correção, parse estruturado direto para o schema Pydantic.
    """

    def __init__(self) -> None:
        self.__llm = get_chat_model().with_structured_output(AgentCorrection)
        self.__prompt = ChatPromptTemplate.from_messages([
            ("human", CORRECTOR_SYSTEM_PROMPT)
        ])
        self.__chain = self.__prompt | self.__llm
        self.__logger = get_logger(__name__)

    @traceable(run_type="chain", name="Examiner Agent Evaluation")
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    async def evaluate(
        self,
        agent_id: AgentID,
        question: ExamQuestion,
        student_answer: StudentAnswer,
        rag_contexts: List[RetrievedContext]
    ) -> AgentCorrection:
        """
        Executa correcao de uma resposta de aluno.

        Args:
            agent_id: Identificador do agente (CORRETOR_1 ou CORRETOR_2)
            question: Questao com enunciado e rubrica
            student_answer: Resposta discursiva do aluno
            rag_contexts: Contextos recuperados via RAG

        Returns:
            AgentCorrection: Resultado estruturado da avaliacao
        """
        self.__logger.info(
            "[%s] Iniciando avaliacao da questao %s para resposta do aluno %s",
            agent_id, question.id, student_answer.student_id
        )

        result: AgentCorrection = await self.__chain.ainvoke({
            "question_statement": question.statement,
            "rubric_formatted": format_rubric_text(question.rubric),
            "rag_context_formatted": format_rag_context(rag_contexts),
            "student_answer": student_answer.text,
            "agent_id": agent_id,
        })

        result.agent_id = agent_id

        self.__logger.info(
            "[%s] Avaliacao concluida. Nota atribuida: %.2f",
            agent_id, result.total_score
        )
        return result
