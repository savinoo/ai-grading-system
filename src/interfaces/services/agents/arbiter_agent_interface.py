from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.rag_schemas import RetrievedContext
from src.domain.ai.agent_schemas import AgentCorrection

class ArbiterAgentInterface(ABC):
    """
    Interface para o serviço de agente árbitro (Arbiter).
    """
    
    @abstractmethod
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
            AgentCorrection: Resultado estruturado da arbitragem
        """
        raise NotImplementedError()
