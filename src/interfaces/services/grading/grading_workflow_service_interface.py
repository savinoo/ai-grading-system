from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.rag_schemas import RetrievedContext

class GradingWorkflowServiceInterface(ABC):
    """
    Interface para o serviço de workflow de correção automática.
    """
    
    @abstractmethod
    async def grade_single_answer(
        self,
        db: Session,
        exam_uuid: UUID,
        question: ExamQuestion,
        student_answer: StudentAnswer,
        *,
        rag_contexts: Optional[List[RetrievedContext]] = None
    ) -> Dict:
        """
        Executa workflow completo de correção usando LangGraph.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova (para filtrar RAG)
            question: Questão com enunciado e rubrica
            student_answer: Resposta discursiva do aluno
        
        Returns:
            Dict com final_score, all_corrections, divergence_detected
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def grade_exam(self, db: Session, exam_uuid: UUID) -> Dict:
        """
        Corrige todas as respostas de todas as questões da prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova a ser corrigida
        
        Returns:
            Dict com estatísticas da correção
        """
        raise NotImplementedError()
