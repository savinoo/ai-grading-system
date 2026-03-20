from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.orm import Session

from src.domain.responses.exam_question_criteria_override.criteria_override_response import ExamQuestionCriteriaOverrideResponse


class ListQuestionCriteriaOverridesServiceInterface(ABC):
    """
    Interface para serviço de listagem de critérios customizados de uma questão.
    """

    @abstractmethod
    async def list_question_criteria_overrides(
        self,
        db: Session,
        question_uuid: str,
        teacher_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[ExamQuestionCriteriaOverrideResponse]:
        """
        Lista critérios customizados de uma questão.
        
        Args:
            db: Sessão do banco de dados
            question_uuid: UUID da questão
            teacher_uuid: UUID do professor autenticado
            skip: Número de registros a pular
            limit: Número máximo de registros a retornar
            active_only: Se deve retornar apenas critérios ativos
            
        Returns:
            List[ExamQuestionCriteriaOverrideResponse]: Lista de critérios customizados
            
        Raises:
            ValidateError: Se a questão não existe ou não pertence ao professor
            SqlError: Em caso de erro de banco de dados
        """
        raise NotImplementedError
