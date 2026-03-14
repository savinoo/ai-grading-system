import logging

from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.prompts import ARBITER_SYSTEM_PROMPT, format_rag_context, format_rubric_text
from src.domain.schemas import AgentCorrection, AgentID
from src.domain.state import GraphState
from src.infrastructure.llm_factory import get_chat_model
from src.utils.helpers import measure_time

logger = logging.getLogger(__name__)

# NOTE: DSPy removido do runtime — ver dspy_examiner.py para justificativa arquitetural.


class DSPyArbiterAgent:
    """
    Agente Árbitro (C3) — ativa somente quando |C1 - C2| > DIVERGENCE_THRESHOLD.

    Usa LangChain with_structured_output(AgentCorrection): 1 chamada LLM, parse direto.
    O nome da classe mantém compatibilidade com nodes.py e __init__.py.
    """

    def __init__(self):
        self._llm = get_chat_model().with_structured_output(AgentCorrection)
        self._prompt = ChatPromptTemplate.from_messages([
            ("human", ARBITER_SYSTEM_PROMPT)
        ])
        self._chain = self._prompt | self._llm

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(10),
        reraise=True
    )
    @traceable(name="Arbiter Decision", run_type="chain")
    async def arbitrate(self, state: GraphState) -> AgentCorrection:
        logger.info("[ARBITER] Iniciando processo de desempate...")

        question = state["question"]
        student_answer = state["student_answer"]
        rag_context = state["rag_context"]

        c1 = next(c for c in state["individual_corrections"] if c.agent_id == AgentID.CORRETOR_1)
        c2 = next(c for c in state["individual_corrections"] if c.agent_id == AgentID.CORRETOR_2)

        with measure_time(f"Arbiter - Question {question.id}"):
            result: AgentCorrection = await self._chain.ainvoke({
                "question_statement": question.statement,
                "rubric_formatted": format_rubric_text(question.rubric),
                "rag_context_formatted": format_rag_context(rag_context),
                "student_answer": student_answer.text,
                "score_c1": c1.total_score,
                "score_c2": c2.total_score,
                "divergence_value": round(abs(c1.total_score - c2.total_score), 2),
                "reasoning_c1": c1.reasoning_chain,
                "reasoning_c2": c2.reasoning_chain,
            })

        result.agent_id = AgentID.ARBITER
        result.calculate_total_if_missing()

        logger.info(f"[ARBITER] Desempate concluído. Nota final: {result.total_score}")
        return result
