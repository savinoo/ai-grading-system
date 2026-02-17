from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.requests.reviews import AdjustGradeRequest

from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.services.reviews.grade_adjustment_service_interface import GradeAdjustmentServiceInterface

from src.models.entities.student_answer_criteria_scores import StudentAnswerCriteriaScore
from src.models.entities.student_answers import StudentAnswer

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError
from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger


class GradeAdjustmentService(GradeAdjustmentServiceInterface):
    """Serviço para ajuste de notas."""
    
    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface
    ):
        self.__exam_repository = exam_repository
        self.__student_answer_repository = student_answer_repository
        self.__logger = get_logger(__name__)
    
    def adjust_grade(
        self,
        db: Session,
        request: AdjustGradeRequest,
        user_uuid: UUID
    ) -> dict:
        """Ajusta nota manualmente."""
        
        # Buscar resposta
        answer = self.__student_answer_repository.get_by_uuid(db, request.answer_uuid)
        if not answer:
            raise NotFoundError(f"Resposta {request.answer_uuid} não encontrada")
        
        # Buscar prova para validar permissão
        exam = self.__exam_repository.get_by_uuid(db, answer.exam_uuid)
        if not exam:
            raise NotFoundError("Prova não encontrada")
        
        if str(exam.created_by) != str(user_uuid):
            raise UnauthorizedError("Você não tem permissão para modificar esta correção")
        
        # Validar nova nota
        if request.new_score < 0:
            raise ValidateError("A nota não pode ser negativa")
        
        # Atualizar nota
        answer.score = request.new_score
        
        # Atualizar feedback se fornecido
        if request.feedback is not None:
            answer.feedback = request.feedback
        
        # Atualizar quem fez o grading
        answer.graded_by = user_uuid
        answer.graded_at = db.execute(
            db.query(StudentAnswer).filter(StudentAnswer.uuid == answer.uuid)
        ).scalar_one().updated_at
        
        # Ajustar scores por critério se fornecido
        if request.criteria_adjustments:
            for criterion_uuid_str, new_score in request.criteria_adjustments.items():
                criterion_uuid = UUID(criterion_uuid_str)
                
                # Buscar score do critério
                criteria_score = db.query(StudentAnswerCriteriaScore).filter(
                    StudentAnswerCriteriaScore.student_answer_uuid == answer.uuid,
                    StudentAnswerCriteriaScore.criteria_uuid == criterion_uuid
                ).first()
                
                if criteria_score:
                    criteria_score.raw_score = new_score
                    # TODO: Buscar peso do exam_criteria para recalcular weighted_score
        
        db.commit()
        db.refresh(answer)
        
        self.__logger.info(
            "Nota ajustada para %s pelo usuário %s. Nova nota: %s",
            request.answer_uuid,
            user_uuid,
            request.new_score
        )
        
        return {
            "message": "Nota ajustada com sucesso",
            "answer_uuid": str(request.answer_uuid),
            "new_score": float(answer.score)
        }
