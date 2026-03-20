from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.services.reviews.answer_approval_service_interface import AnswerApprovalServiceInterface

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


class AnswerApprovalService(AnswerApprovalServiceInterface):
    """Serviço para aprovação individual de respostas."""
    
    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface
    ):
        self.__exam_repository = exam_repository
        self.__student_answer_repository = student_answer_repository
        self.__logger = get_logger(__name__)
    
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
        
        # Buscar resposta
        answer = self.__student_answer_repository.get_by_uuid(db, answer_uuid)
        if not answer:
            raise NotFoundError(f"Resposta {answer_uuid} não encontrada")
        
        # Buscar prova para validar permissão
        exam = self.__exam_repository.get_by_uuid(db, answer.exam_uuid)
        if not exam:
            raise NotFoundError("Prova não encontrada")
        
        if str(exam.created_by) != str(user_uuid):
            raise UnauthorizedError("Você não tem permissão para aprovar esta correção")
        
        # Validar que a resposta está em estado correto (deve estar GRADED)
        if answer.status != 'GRADED':
            raise ValidateError(
                f"Apenas respostas com status GRADED podem ser aprovadas. Status atual: {answer.status}"
            )
        
        # Validar que a resposta tem nota
        if answer.score is None:
            raise ValidateError("Resposta sem nota não pode ser aprovada")
        
        # Atualizar status para FINALIZED
        answer.status = 'FINALIZED'
        
        # Marcar quem aprovou e quando
        answer.graded_by = user_uuid
        answer.graded_at = datetime.utcnow()
        
        db.commit()
        db.refresh(answer)
        
        self.__logger.info(
            "Resposta %s aprovada pelo usuário %s",
            answer_uuid,
            user_uuid
        )
        
        return {
            "message": "Resposta aprovada com sucesso",
            "answer_uuid": str(answer.uuid),
            "status": answer.status,
            "score": float(answer.score) if answer.score else None,
            "graded_by": str(answer.graded_by),
            "graded_at": answer.graded_at.isoformat() if answer.graded_at else None
        }
