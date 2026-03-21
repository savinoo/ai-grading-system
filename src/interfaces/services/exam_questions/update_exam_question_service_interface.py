from __future__ import annotations

from uuid import UUID
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.requests.exam_questions.exam_question_update_request import ExamQuestionUpdateRequest
from src.domain.responses.exam_questions.exam_question_response import ExamQuestionResponse

class UpdateExamQuestionServiceInterface(ABC):
    """
    Interface para serviço de atualização de questão de prova.
    """

    @abstractmethod
    async def update_exam_question(
        self,
        db: Session,
        question_uuid: UUID,
        teacher_uuid: UUID,
        request: ExamQuestionUpdateRequest
    ) -> ExamQuestionResponse:
        """
        Atualiza uma questão existente.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão a ser atualizada
            teacher_uuid: UUID do professor (para validação)
            request: Dados a serem atualizados
            
        Returns:
            ExamQuestionResponse: Questão atualizada
            
        Raises:
            ValidateError: Se a questão não existir ou o professor não tiver permissão
            SqlError: Se houver erro no banco de dados
        """
        raise NotImplementedError()
