import logging

from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.prompts import CORRECTOR_SYSTEM_PROMPT, format_rag_context, format_rubric_text
from src.domain.schemas import AgentCorrection, AgentID
from src.domain.state import GraphState
from src.infrastructure.llm_factory import get_chat_model
from src.utils.helpers import measure_time

logger = logging.getLogger(__name__)

# NOTE: DSPy foi removido do runtime de correção (refactor arquitetural).
# Motivo: DSPy é um framework de OTIMIZAÇÃO de prompts (offline), não de inferência runtime.
# Usar DSPy.TypedPredictor a cada correção adicionava 1-3 chamadas extras desnecessárias ao LLM.
# Arquitetura correta:
#   - Offline: DSPy BootstrapFewShot otimiza o prompt com exemplos reais (quando disponíveis)
#   - Runtime: LangChain with_structured_output → 1 chamada garantida, parsing confiável


class DSPyExaminerAgent:
    """
    Agente Corretor Independente (C1 ou C2).

    Usa LangChain with_structured_output(AgentCorrection) para inferência runtime:
    1 chamada LLM por correção, parse estruturado direto para o schema Pydantic.

    O nome da classe mantém compatibilidade com nodes.py e __init__.py.
    DSPy permanece disponível apenas para otimização offline de prompts.
    """

    def __init__(self):
        self._llm = get_chat_model().with_structured_output(AgentCorrection)
        self._prompt = ChatPromptTemplate.from_messages([
            ("human", CORRECTOR_SYSTEM_PROMPT)
        ])
        self._chain = self._prompt | self._llm

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(10),
        reraise=True
    )
    @traceable(name="Examiner Evaluation", run_type="chain")
    async def evaluate(self, state: GraphState, agent_id: AgentID) -> AgentCorrection:
        question = state["question"]
        student_answer = state["student_answer"]
        rag_context = state["rag_context"]

        logger.info(f"[{agent_id}] Iniciando avaliação da questão {question.id}...")

        with measure_time(f"Examiner {agent_id} - Question {question.id}"):
            result: AgentCorrection = await self._chain.ainvoke({
                "question_statement": question.statement,
                "rubric_formatted": format_rubric_text(question.rubric),
                "rag_context_formatted": format_rag_context(rag_context),
                "student_answer": student_answer.text,
                "agent_id": agent_id,
            })

        result.agent_id = agent_id
        result.calculate_total_if_missing()

        logger.info(f"[{agent_id}] Avaliação concluída. Nota: {result.total_score}")
        return result
