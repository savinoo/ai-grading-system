from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.orm import Session

from src.domain.responses.exam_questions.exam_question_response import ExamQuestionResponse

class ListExamQuestionsServiceInterface(ABC):
    """
    Interface para serviço de listagem de questões de prova.
    """

    @abstractmethod
    async def list_exam_questions(
        self,
        db: Session,
        exam_uuid: str,
        teacher_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[ExamQuestionResponse]:
        """
        Lista questões de uma prova.
        
        Args:
            db: Sessão do banco de dados
            exam_uuid: UUID da prova
            teacher_uuid: UUID do professor autenticado
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas questões ativas
            
        Returns:
            List[ExamQuestionResponse]: Lista de questões da prova
        """
        raise NotImplementedError()
