from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.requests.classes.class_create_request import ClassCreateRequest
from src.domain.responses.classes.class_create_response import ClassCreateResponse

class CreateClassServiceInterface(ABC):
    """
    Interface para o serviço de criação de turmas.
    """
    
    @abstractmethod
    async def create_class(
        self,
        db: Session,
        request: ClassCreateRequest,
        teacher_uuid: UUID
    ) -> ClassCreateResponse:
        """
        Cria uma nova turma.
        
        Args:
            db: Sessão do banco de dados
            request: Dados da turma a ser criada
            teacher_uuid: UUID do professor que está criando a turma
            
        Returns:
            ClassCreateResponse: Dados da turma criada
        """
        raise NotImplementedError()
