import dspy
import logging
import asyncio
from langsmith import traceable
from src.domain.schemas import AgentCorrection, AgentID
from src.domain.state import GraphState
from src.config.settings import settings
from src.config.prompts import format_rubric_text, format_rag_context
from src.infrastructure.dspy_config import configure_dspy

logger = logging.getLogger(__name__)

# Garante a configuração
configure_dspy()

class GradingSignature(dspy.Signature):
    """
    Avalie a resposta do aluno com base na rubrica detalhada e no contexto fornecido.
    Siga rigorosamente os critérios de avaliação.
    Gere um raciocínio detalhado (CoT) antes de atribuir as notas.
    """
    question_statement = dspy.InputField(desc="O enunciado da questão da prova")
    rubric_formatted = dspy.InputField(desc="A rubrica de avaliação detalhada com critérios e pesos")
    rag_context_formatted = dspy.InputField(desc="Trechos relevantes do material didático (RAG)")
    student_answer = dspy.InputField(desc="A resposta discursiva submetida pelo aluno")
    
    correction = dspy.OutputField(desc="A correção estruturada contendo raciocínio, notas e feedback", type=AgentCorrection)

class DSPyExaminerModule(dspy.Module):
    def __init__(self):
        super().__init__()
        # Ajuste para compatibilidade com versões do DSPy onde TypedPredictor foi renomeado ou integrado
        # Em DSPy moderno, ChainOfThought com assinatura tipada já tenta fazer o parsing
        try:
             self.grading = dspy.TypedPredictor(GradingSignature)
        except AttributeError:
             # Fallback para versão onde TypedPredictor não está no topo ou v3+ que usa Predict integrado
             # Usamos ChainOfThought que é melhor para nossa usecase (precisa de raciocínio)
             self.grading = dspy.ChainOfThought(GradingSignature)

    def forward(self, question_statement, rubric_formatted, rag_context_formatted, student_answer):
        return self.grading(
            question_statement=question_statement,
            rubric_formatted=rubric_formatted,
            rag_context_formatted=rag_context_formatted,
            student_answer=student_answer
        )

class DSPyExaminerAgent:
    """
    Versão DSPy do ExaminerAgent.
    Substitui o pipeline LangChain pelo dspy.TypedPredictor para melhor otimização e estrutura.
    """
    def __init__(self):
        self.module = DSPyExaminerModule()

    @traceable(name="DSPy Examiner Evaluation", run_type="chain")
    async def evaluate(self, state: GraphState, agent_id: AgentID) -> AgentCorrection:
        """
        Executa a avaliação usando DSPy.
        """
        question = state["question"]
        student_answer = state["student_answer"]
        rag_context = state["rag_context"]

        formatted_rubric = format_rubric_text(question.rubric)
        formatted_context = format_rag_context(rag_context)

        logger.info(f"[{agent_id}] (DSPy) Iniciando avaliação da questão {question.id}...")

        # Execução síncrona do DSPy encapsulada em thread para não bloquear o loop async
        loop = asyncio.get_event_loop()
        
        def run_prediction():
            return self.module(
                question_statement=question.statement,
                rubric_formatted=formatted_rubric,
                rag_context_formatted=formatted_context,
                student_answer=student_answer.text
            )

        try:
            prediction = await loop.run_in_executor(None, run_prediction)
            
            # Tratamento robusto para retorno do DSPy (Objeto vs String vs Dict)
            raw_result = prediction.correction
            
            if isinstance(raw_result, AgentCorrection):
                result = raw_result
            elif isinstance(raw_result, str):
                # Se voltou string (às vezes acontece em fallbacks), parseamos manualmente
                # Remove markdown code blocks se houver
                clean_json = raw_result.replace("```json", "").replace("```", "").strip()
                result = AgentCorrection.model_validate_json(clean_json)
            elif isinstance(raw_result, dict):
                 result = AgentCorrection.model_validate(raw_result)
            else:
                 # Tentativa final: talvez seja um objeto Prediction aninhado
                 result = AgentCorrection.model_validate(raw_result)

            # Garante que o ID do agente está correto e recupera CoT antigo se vier separado
            # Se usou ChainOfThought, o raciocínio pode estar em prediction.rationale ou prediction.reasoning
            if hasattr(prediction, 'rationale'):
                 # Se o reasoning dentro do JSON estiver vazio, usamos o do DSPy
                 if not result.reasoning_chain: 
                     result.reasoning_chain = prediction.rationale

            result.agent_id = agent_id
            
            # Recalcula total score por segurança (via validador do Pydantic)
            result.calculate_total_if_missing()
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no DSPy Examiner: {e}")
            raise e
