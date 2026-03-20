from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.rag_schemas import RetrievedContext
from src.domain.ai.agent_schemas import AgentCorrection, AgentID

class ExaminerAgentInterface(ABC):
    """
    Interface para o serviço de agente corretor (Examiner).
    """
    
    @abstractmethod
    async def evaluate(
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
            rag_contexts: Contextos recuperados via RAG
        
        Returns:
            AgentCorrection: Resultado estruturado da avaliação
        """
        raise NotImplementedError()
