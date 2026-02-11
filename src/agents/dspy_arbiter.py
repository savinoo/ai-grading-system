import dspy
import logging
import asyncio
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.domain.schemas import AgentCorrection, AgentID
from src.domain.state import GraphState
from src.config.settings import settings
from src.config.prompts import format_rubric_text, format_rag_context
from src.utils.helpers import measure_time
# from src.infrastructure.dspy_config import configure_dspy # REMOVIDO

logger = logging.getLogger(__name__)

# Garante a configuração
# configure_dspy()

class ArbitrationSignature(dspy.Signature):
    """
    Atue como um Árbitro Sênior para desempatar avaliações divergentes.
    Analise o enunciado, o contexto (RAG), a resposta do aluno e os argumentos dos dois corretores anteriores.
    Decida a nota final de forma independente e justificada.
    """
    question_statement = dspy.InputField(desc="O enunciado da questão da prova")
    rubric_formatted = dspy.InputField(desc="A rubrica de avaliação detalhada")
    rag_context_formatted = dspy.InputField(desc="Trechos relevantes do material didático (referência a seguir)")
    student_answer = dspy.InputField(desc="A resposta do aluno sob disputa")
    
    # Inputs específicos do árbitro
    corrector_1_evaluation = dspy.InputField(desc="Argumentos e nota do Corretor 1")
    corrector_2_evaluation = dspy.InputField(desc="Argumentos e nota do Corretor 2")
    divergence_context = dspy.InputField(desc="Cálculo da divergência encontrada entre os corretores")
    
    arbitration = dspy.OutputField(desc="O veredito final estruturado contendo a nova correção de desempate")

class DSPyArbiterModule(dspy.Module):
    def __init__(self):
        super().__init__()
        # Ajuste para compatibilidade com versões do DSPy
        try:
            self.arbitrate = dspy.TypedPredictor(ArbitrationSignature)
        except AttributeError:
             # Fallback: Usar ChainOfThought com assinatura tipada
            self.arbitrate = dspy.ChainOfThought(ArbitrationSignature)

    def forward(self, **kwargs):
        return self.arbitrate(**kwargs)

class DSPyArbiterAgent:
    """
    Versão DSPy do ArbiterAgent.
    Substitui a lógica de prompt manual por um m´dulo DSPy tipado.
    """
    def __init__(self):
        self.module = DSPyArbiterModule()

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(10),
        reraise=True
    )
    @traceable(name="DSPy Arbiter Decision", run_type="chain")
    async def arbitrate(self, state: GraphState) -> AgentCorrection:
        """
        Executa a arbitragem usando DSPy.
        """
        try:
            logger.info("[DSPy ARBITER] Iniciando processo de desempate...")

            # 1. Extração dos dados do Estado
            question = state["question"]
            student_answer = state["student_answer"]
            rag_context = state["rag_context"]
            
            # Encontra as correções anteriores
            c1_correction = next(c for c in state["individual_corrections"] if c.agent_id == AgentID.CORRETOR_1)
            c2_correction = next(c for c in state["individual_corrections"] if c.agent_id == AgentID.CORRETOR_2)
            
            # Formatações
            formatted_rubric = format_rubric_text(question.rubric)
            formatted_context = format_rag_context(rag_context)
            
            # Prepara o resumo das avaliações anteriores para o Árbitro
            c1_text = f"Nota Total: {c1_correction.total_score}\nRaciocínio: {c1_correction.reasoning_chain}"
            c2_text = f"Nota Total: {c2_correction.total_score}\nRaciocínio: {c2_correction.reasoning_chain}"
            div_text = f"Divergência detectada: {abs(c1_correction.total_score - c2_correction.total_score)} pontos."

            # Execução síncrona encapsulada (mesmo padrão do Examiner)
            loop = asyncio.get_running_loop()
            
            def run_arbitration():
                with measure_time(f"DSPy Arbiter - Question {question.id}"):
                    return self.module(
                        question_statement=question.statement,
                        rubric_formatted=formatted_rubric,
                        rag_context_formatted=formatted_context,
                        student_answer=student_answer.text,
                        corrector_1_evaluation=c1_text,
                        corrector_2_evaluation=c2_text,
                        divergence_context=div_text
                    )

            prediction = await loop.run_in_executor(None, run_arbitration)
            
            # Tratamento robusto para retorno do DSPy
            raw_result = prediction.arbitration
            
            if isinstance(raw_result, AgentCorrection):
                result = raw_result
            elif isinstance(raw_result, str):
                import json as _json
                clean_json = raw_result.replace("```json", "").replace("```", "").strip()
                data = _json.loads(clean_json)
                if isinstance(data, dict) and "agent_id" not in data:
                    data["agent_id"] = AgentID.ARBITER
                result = AgentCorrection.model_validate(data)
            elif isinstance(raw_result, dict):
                if "agent_id" not in raw_result:
                    raw_result["agent_id"] = AgentID.ARBITER
                result = AgentCorrection.model_validate(raw_result)
            else:
                # Try validating unknown shapes
                result = AgentCorrection.model_validate(raw_result)

            if hasattr(prediction, 'rationale') and not result.reasoning_chain:
                result.reasoning_chain = prediction.rationale

            result.agent_id = AgentID.ARBITER
            result.calculate_total_if_missing()
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no DSPy Arbiter: {e}")
            # Em caso de falha crítica do DSPy, poderíamos ter um fallback aqui, 
            # mas vamos apenas propagar o erro por enquanto.
            raise e
