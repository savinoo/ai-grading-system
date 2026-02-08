from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.requests.exam_questions.exam_question_create_request import ExamQuestionCreateRequest
from src.domain.responses.exam_questions.exam_question_response import ExamQuestionResponse

class CreateExamQuestionServiceInterface(ABC):
    """
    Interface para serviço de criação de questão de prova.
    """

    @abstractmethod
    async def create_exam_question(
        self,
        db: Session,
        request: ExamQuestionCreateRequest
    ) -> ExamQuestionResponse:
        """
        Cria uma nova questão para uma prova.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da questão a ser criada
            
        Returns:
            ExamQuestionResponse: Dados da questão criada
        """
        raise NotImplementedError()
