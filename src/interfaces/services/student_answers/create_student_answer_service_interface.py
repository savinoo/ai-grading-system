from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.requests.student_answers.student_answer_create_request import StudentAnswerCreateRequest
from src.domain.responses.student_answers.student_answer_response import StudentAnswerResponse

class CreateStudentAnswerServiceInterface(ABC):
    """
    Interface para serviço de criação de resposta de aluno.
    """

    @abstractmethod
    async def create_student_answer(
        self,
        db: Session,
        request: StudentAnswerCreateRequest
    ) -> StudentAnswerResponse:
        """
        Cria uma nova resposta de aluno.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da resposta a ser criada
            
        Returns:
            StudentAnswerResponse: Dados da resposta criada
        """
        raise NotImplementedError()
