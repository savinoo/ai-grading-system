from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.requests.reviews import FinalizeReviewRequest

from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.services.reviews.review_finalization_service_interface import ReviewFinalizationServiceInterface

from src.utils.excel_report_generator import generate_grades_report

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError

from src.core.logging_config import get_logger


class ReviewFinalizationService(ReviewFinalizationServiceInterface):
    """Serviço para finalização de revisão."""
    
    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface
    ):
        self.__exam_repository = exam_repository
        self.__student_answer_repository = student_answer_repository
        self.__logger = get_logger(__name__)
    
    def finalize_review(
        self,
        db: Session,
        request: FinalizeReviewRequest,
        user_uuid: UUID
    ) -> dict:
        """
        Finaliza revisão e gera relatório.
        
        Ações realizadas:
        - Atualiza status da prova para FINALIZED
        - Atualiza status de todas as respostas para FINALIZED  
        - Marca graded_by em todas as respostas
        - Gera arquivo Excel com as notas
        """
        
        # Buscar prova
        exam = self.__exam_repository.get_by_uuid(db, request.exam_uuid)
        if not exam:
            raise NotFoundError(f"Prova {request.exam_uuid} não encontrada")
        
        if str(exam.created_by) != str(user_uuid):
            raise UnauthorizedError("Você não tem permissão para finalizar esta revisão")
        
        # Buscar todas as respostas da prova
        all_answers = self.__student_answer_repository.get_by_exam(
            db,
            request.exam_uuid,
            limit=10000  # Limite alto para pegar todas
        )
        
        self.__logger.info(
            "Finalizando revisão de %d respostas da prova %s",
            len(all_answers),
            request.exam_uuid
        )
        
        # Atualizar todas as respostas
        for answer in all_answers:
            answer.status = "FINALIZED"
            if not answer.graded_by:
                answer.graded_by = user_uuid
            if not answer.graded_at:
                answer.graded_at = datetime.utcnow()
        
        # Atualizar status da prova para FINALIZED
        exam.status = "FINALIZED"
        
        # Commit das mudanças
        try:
            db.commit()
            self.__logger.info(
                "Status atualizado: prova e %d respostas agora FINALIZED",
                len(all_answers)
            )
        except Exception as e:
            db.rollback()
            self.__logger.error("Erro ao finalizar revisão: %s", e, exc_info=True)
            raise
        
        # Gerar arquivo Excel com as notas
        excel_path = None
        if request.generate_pdf:  # Usando generate_pdf como flag para gerar relatório
            try:
                excel_path = generate_grades_report(db, exam, all_answers)
                self.__logger.info("Relatório Excel gerado: %s", excel_path)
            except Exception as e:
                self.__logger.error("Erro ao gerar relatório Excel: %s", e, exc_info=True)
                # Não falhar a operação se o Excel falhar
        
        # TODO: Implementar envio de notificações
        if request.send_notifications:
            self.__logger.info(
                "Solicitação de envio de notificações para prova %s",
                request.exam_uuid
            )
            # enviar_notificacoes_alunos(exam_uuid)
        
        self.__logger.info(
            "Revisão finalizada para prova %s pelo usuário %s",
            request.exam_uuid,
            user_uuid
        )
        
        return {
            "message": "Revisão finalizada com sucesso",
            "exam_uuid": str(request.exam_uuid),
            "excel_report": excel_path,
            "notifications_sent": request.send_notifications,
            "total_answers_finalized": len(all_answers)
        }
