from uuid import UUID
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

class AnswerApprovalServiceInterface(ABC):
    """Serviço para aprovação individual de respostas."""
    
    @abstractmethod
    def approve_answer(
        self,
        db: Session,
        answer_uuid: UUID,
        user_uuid: UUID
    ) -> dict:
        """
        Aprova uma resposta individual, marcando-a como finalizada.
        
        Args:
            db: Sessão do banco de dados
            answer_uuid: UUID da resposta a ser aprovada
            user_uuid: UUID do usuário que está aprovando
            
        Returns:
            Dicionário com mensagem de sucesso e dados da resposta
            
        Raises:
            NotFoundError: Se a resposta ou prova não for encontrada
            UnauthorizedError: Se o usuário não tiver permissão
            ValidateError: Se a resposta não estiver em estado válido
        """
        raise NotImplementedError()
