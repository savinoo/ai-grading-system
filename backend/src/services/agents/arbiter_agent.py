from __future__ import annotations

import asyncio
from typing import List

import dspy
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

from src.interfaces.services.agents.arbiter_agent_interface import ArbiterAgentInterface

from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.rag_schemas import RetrievedContext
from src.domain.ai.agent_schemas import AgentCorrection, AgentID, CriterionScore
from src.domain.ai.prompts import format_rubric_text, format_rag_context

from src.errors.domain.sql_error import SqlError

from src.core.settings import settings
from src.core.logging_config import get_logger


# =============================================================================
# DSPy Signature para Arbitragem
# =============================================================================

class ArbitrationSignature(dspy.Signature):
    """
    Assinatura DSPy para arbitragem de avaliações divergentes.
    
    O Árbitro analisa a resposta do aluno, o contexto RAG e as duas avaliações
    anteriores (Corretor 1 e Corretor 2) para emitir um veredito final de desempate.
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
    
    # Inputs específicos do árbitro
    corrector_1_evaluation: str = dspy.InputField(
        desc="Argumentos (reasoning_chain) e nota do Corretor 1"
    )
    corrector_2_evaluation: str = dspy.InputField(
        desc="Argumentos (reasoning_chain) e nota do Corretor 2"
    )
    divergence_context: str = dspy.InputField(
        desc="Informação sobre a divergência detectada entre os corretores"
    )
    
    # Outputs estruturados
    reasoning_chain: str = dspy.OutputField(
        desc="Raciocínio do árbitro analisando os argumentos de ambos os corretores "
             "e justificando a decisão final (mínimo 50 caracteres)."
    )
    criteria_scores: List[dict] = dspy.OutputField(
        desc="Lista de dicionários com {criterion_name: str, score: float, max_score: float, feedback: str} "
             "para cada critério da rubrica, com a decisão independente do árbitro. "
             "O max_score deve ser extraído da rubrica fornecida (campo 'Nota Máxima')."
    )
    total_score: float = dspy.OutputField(
        desc="Nota final de desempate calculada como SOMA das notas individuais"
    )


# =============================================================================
# DSPy Module
# =============================================================================

class DSPyArbiterModule(dspy.Module):
    """
    Módulo DSPy para arbitragem estruturada com Chain-of-Thought.
    """
    
    def __init__(self):
        super().__init__()
        # ChainOfThought para raciocínio detalhado do árbitro
        self.predictor = dspy.ChainOfThought(ArbitrationSignature)
    
    def forward(self, **kwargs):
        """
        Executa a predição do árbitro.
        
        Returns:
            Objeto DSPy com campos: reasoning_chain, criteria_scores, total_score
        """
        return self.predictor(**kwargs)


# =============================================================================
# Arbiter Agent
# =============================================================================

class ArbiterAgent(ArbiterAgentInterface):
    """
    Serviço de agente árbitro usando DSPy para desempate de avaliações divergentes.
    
    É chamado quando a diferença entre as notas de CORRETOR_1 e CORRETOR_2
    excede o limiar de divergência configurado (DIVERGENCE_THRESHOLD).
    """
    
    def __init__(self) -> None:
        """Inicializa o módulo DSPy de arbitragem."""
        self.__dspy_module = DSPyArbiterModule()
        self.__logger = get_logger(__name__)
    
    @traceable(run_type="chain", name="Arbiter Agent Decision")
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def evaluate(  # type: ignore[override]  # pylint: disable=arguments-differ
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
        
        Raises:
            SqlError: Se houver falha na comunicação com o LLM após retries
        """
        self.__logger.info(
            "[ARBITER] Iniciando arbitragem para questão %s (divergência: %.2f pontos)",
            question.id, abs(correction_1.total_score - correction_2.total_score)
        )
        
        # Formatar inputs
        rubric_text = format_rubric_text(question.rubric)
        rag_text = format_rag_context(rag_contexts)
        
        # Preparar resumo das avaliações anteriores
        c1_text = (
            f"Nota Total: {correction_1.total_score:.2f}\n"
            f"Raciocínio:\n{correction_1.reasoning_chain}\n"
            f"Notas por Critério:\n" +
            "\n".join([
                f"  - {cs.criterion_name}: {cs.score:.2f} ({cs.feedback})"
                for cs in correction_1.criteria_scores
            ])
        )
        
        c2_text = (
            f"Nota Total: {correction_2.total_score:.2f}\n"
            f"Raciocínio:\n{correction_2.reasoning_chain}\n"
            f"Notas por Critério:\n" +
            "\n".join([
                f"  - {cs.criterion_name}: {cs.score:.2f} ({cs.feedback})"
                for cs in correction_2.criteria_scores
            ])
        )
        
        div_text = (
            f"Divergência detectada: {abs(correction_1.total_score - correction_2.total_score):.2f} pontos\n"
            f"Limiar configurado: {settings.DIVERGENCE_THRESHOLD} pontos\n"
            f"Corretor 1: {correction_1.total_score:.2f} | Corretor 2: {correction_2.total_score:.2f}"
        )
        
        # DSPy é síncrono - executamos em thread pool
        loop = asyncio.get_event_loop()
        
        def run_dspy_arbitration():
            """Closure para executar DSPy de forma síncrona."""
            return self.__dspy_module(
                question_statement=question.statement,
                rubric_formatted=rubric_text,
                rag_context_formatted=rag_text,
                student_answer=student_answer.text,
                corrector_1_evaluation=c1_text,
                corrector_2_evaluation=c2_text,
                divergence_context=div_text
            )
        
        try:
            # Executa DSPy em thread separada
            prediction = await loop.run_in_executor(None, run_dspy_arbitration)
            
            self.__logger.debug("[ARBITER] DSPy prediction type: %s", type(prediction))
            
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
                    self.__logger.warning("[ARBITER] Formato inesperado em criteria_scores: %s", item)
                    criteria_scores.append(
                        CriterionScore(
                            criterion_name=str(getattr(item, 'criterion_name', 'Unknown')),
                            score=float(getattr(item, 'score', 0.0)),
                            feedback=str(getattr(item, 'feedback', ''))
                        )
                    )
            
            # Criar AgentCorrection estruturado com agent_id=ARBITER
            correction = AgentCorrection(
                agent_id=AgentID.ARBITER,
                reasoning_chain=raw_reasoning,
                criteria_scores=criteria_scores,
                total_score=raw_total_score
            )
            
            self.__logger.info(
                "[ARBITER] Arbitragem concluída. Nota final: %.2f",
                correction.total_score
            )
            self.__logger.debug(
                "[ARBITER] Comparação - C1: %.2f | C2: %.2f | Árbitro: %.2f",
                correction_1.total_score, correction_2.total_score, correction.total_score
            )
            
            return correction
            
        except Exception as e:
            self.__logger.error(
                "[ARBITER] Erro durante arbitragem da questão %s: %s",
                question.id, e,
                exc_info=True
            )
            raise SqlError(
                message="Erro ao arbitrar avaliações divergentes",
                context={
                    "question_id": str(question.id),
                    "student_id": str(student_answer.student_id),
                    "divergence": abs(correction_1.total_score - correction_2.total_score)
                },
                cause=e
            ) from e
