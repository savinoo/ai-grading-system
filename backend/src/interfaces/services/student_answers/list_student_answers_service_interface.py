from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.orm import Session

from src.domain.responses.student_answers.student_answer_response import StudentAnswerResponse


class ListStudentAnswersServiceInterface(ABC):
    """
    Interface para serviço de listagem de respostas de alunos de uma questão.
    """

    @abstractmethod
    async def list_student_answers(
        self,
        db: Session,
        question_uuid: str,
        teacher_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[StudentAnswerResponse]:
        """
        Lista respostas de alunos de uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            teacher_uuid: UUID do professor autenticado
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            
        Returns:
            List[StudentAnswerResponse]: Lista de respostas
            
        Raises:
            ValidateError: Se a questão não existe ou não pertence ao professor
            SqlError: Em caso de erro de banco de dados
        """
        raise NotImplementedError
