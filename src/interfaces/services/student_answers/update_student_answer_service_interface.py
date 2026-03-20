from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.requests.student_answers.student_answer_update_request import StudentAnswerUpdateRequest
from src.domain.responses.student_answers.student_answer_response import StudentAnswerResponse

class UpdateStudentAnswerServiceInterface(ABC):
    """
    Interface para serviço de atualização de resposta de aluno.
    """

    @abstractmethod
    async def update_student_answer(
        self,
        db: Session,
        answer_uuid: UUID,
        request: StudentAnswerUpdateRequest
    ) -> StudentAnswerResponse:
        """
        Atualiza uma resposta de aluno.
        
        Args:
            db: Sessão do banco de dados
            answer_uuid: UUID da resposta
            request: Dados a serem atualizados
            
        Returns:
            StudentAnswerResponse: Dados da resposta atualizada
        """
        raise NotImplementedError()
