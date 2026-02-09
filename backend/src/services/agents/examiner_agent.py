"""
Agente Corretor (Examiner) com DSPy para correção estruturada de respostas.
"""

import logging
import asyncio
from typing import List
import dspy
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.rag_schemas import RetrievedContext
from src.domain.ai.agent_schemas import AgentCorrection, AgentID, CriterionScore
from src.services.agents.base_agent import BaseAgent
from src.services.agents.prompts import format_rubric_text, format_rag_context
from src.core.settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DSPy Signature para Correção
# =============================================================================

class GradingSignature(dspy.Signature):
    """
    Assinatura DSPy para correção estruturada de respostas discursivas.
    
    O LLM deve analisar a resposta do aluno com base na questão, rubrica e
    contexto recuperado via RAG, fornecendo raciocínio Chain-of-Thought e
    notas por critério.
    """
    question_statement: str = dspy.InputField(
        desc="O enunciado completo da questão da prova"
    )
    rubric_formatted: str = dspy.InputField(
        desc="A rubrica de avaliação formatada com critérios e pesos"
    )
    rag_context_formatted: str = dspy.InputField(
        desc="Trechos relevantes do material didático (RAG) como referência"
    )
    student_answer: str = dspy.InputField(
        desc="A resposta discursiva submetida pelo aluno"
    )
    
    # Outputs estruturados
    reasoning_chain: str = dspy.OutputField(
        desc="Raciocínio Chain-of-Thought detalhado ANTES de atribuir notas. "
             "Analise cada critério separadamente (mínimo 50 caracteres)."
    )
    criteria_scores: List[dict] = dspy.OutputField(
        desc="Lista de dicionários com {criterion_name: str, score: float, max_score: float, feedback: str} "
             "para cada critério da rubrica. Use pontuação ABSOLUTA, não percentual. "
             "O max_score deve ser extraído da rubrica fornecida (campo 'Nota Máxima')."
    )
    total_score: float = dspy.OutputField(
        desc="Nota final calculada como SOMA das notas individuais em criteria_scores"
    )


# =============================================================================
# DSPy Module
# =============================================================================

class DSPyExaminerModule(dspy.Module):
    """
    Módulo DSPy para correção estruturada com Chain-of-Thought.
    """
    
    def __init__(self):
        super().__init__()
        # ChainOfThought adiciona raciocínio intermediário antes da resposta final
        self.predictor = dspy.ChainOfThought(GradingSignature)
    
    def forward(
        self,
        question_statement: str,
        rubric_formatted: str,
        rag_context_formatted: str,
        student_answer: str
    ):
        """
        Executa a predição do modelo.
        
        Returns:
            Objeto DSPy com campos: reasoning_chain, criteria_scores, total_score
        """
        return self.predictor(
            question_statement=question_statement,
            rubric_formatted=rubric_formatted,
            rag_context_formatted=rag_context_formatted,
            student_answer=student_answer
        )


# =============================================================================
# Examiner Agent
# =============================================================================

class ExaminerAgent(BaseAgent):
    """
    Agente Corretor usando DSPy para avaliação estruturada.
    
    Pode ser instanciado 2 vezes (CORRETOR_1 e CORRETOR_2) para avaliações
    independentes da mesma resposta.
    
    Attributes:
        dspy_module: Módulo DSPy configurado para correção
    """
    
    def __init__(self):
        """Inicializa o módulo DSPy de correção."""
        self.dspy_module = DSPyExaminerModule()
    
    @traceable(run_type="chain", name="Examiner Agent Evaluation")
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def evaluate(  # type: ignore[override]  # pylint: disable=arguments-differ
        self,
        agent_id: AgentID,
        question: ExamQuestion,
        student_answer: StudentAnswer,
        rag_contexts: List[RetrievedContext]
    ) -> AgentCorrection:
        """
        Executa correção de uma resposta de aluno.
        
        Args:
            agent_id: Identificador do agente (CORRETOR_1 ou CORRETOR_2)
            question: Questão com enunciado e rubrica
            student_answer: Resposta discursiva do aluno
            rag_contexts: Contextos recuperados via RAG para fundamentar a correção
        
        Returns:
            AgentCorrection estruturado com notas, raciocínio e feedback
        
        Raises:
            Exception: Se houver falha na comunicação com o LLM após retries
        """
        logger.info(
            "[%s] Iniciando avaliação da questão %s para resposta do aluno %s",
            agent_id, question.id, student_answer.student_id
        )
        
        # Formatar inputs conforme esperado pelo prompt
        rubric_text = format_rubric_text(question.rubric)
        rag_text = format_rag_context(rag_contexts)
        
        # DSPy é síncrono - executamos em thread pool para não bloquear o loop
        loop = asyncio.get_event_loop()
        
        def run_dspy_prediction():
            """Closure para executar DSPy de forma síncrona."""
            return self.dspy_module(
                question_statement=question.statement,
                rubric_formatted=rubric_text,
                rag_context_formatted=rag_text,
                student_answer=student_answer.text
            )
        
        try:
            # Executa DSPy em thread separada
            prediction = await loop.run_in_executor(None, run_dspy_prediction)
            
            logger.debug("[%s] DSPy prediction type: %s", agent_id, type(prediction))
            
            # Extrair dados da predição DSPy
            raw_reasoning = prediction.reasoning_chain
            raw_criteria_scores = prediction.criteria_scores
            raw_total_score = prediction.total_score
            
            # Converter criteria_scores para CriterionScore Pydantic
            criteria_scores = []
            for item in raw_criteria_scores:
                if isinstance(item, dict):
                    criteria_scores.append(CriterionScore(**item))
                else:
                    # Fallback: tentar extrair campos manualmente
                    logger.warning("[%s] Formato inesperado em criteria_scores: %s", agent_id, item)
                    criteria_scores.append(
                        CriterionScore(
                            criterion_name=str(getattr(item, 'criterion_name', 'Unknown')),
                            score=float(getattr(item, 'score', 0.0)),
                            feedback=str(getattr(item, 'feedback', ''))
                        )
                    )
            
            # Criar AgentCorrection estruturado
            correction = AgentCorrection(
                agent_id=agent_id,
                reasoning_chain=raw_reasoning,
                criteria_scores=criteria_scores,
                total_score=raw_total_score  # Validadores do Pydantic vão recalcular se necessário
            )
            
            logger.info(
                "[%s] Avaliação concluída. Nota atribuída: %.2f",
                agent_id, correction.total_score
            )
            logger.debug("[%s] Critérios avaliados: %d", agent_id, len(correction.criteria_scores))
            
            return correction
            
        except Exception as e:
            logger.error(
                "[%s] Erro durante avaliação da questão %s: %s",
                agent_id, question.id, e,
                exc_info=True
            )
            raise
