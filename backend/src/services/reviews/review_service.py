"""
Serviço para revisão de provas corrigidas pela IA.
"""

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from src.interfaces.services.reviews.review_service_interface import ReviewServiceInterface
from src.domain.responses.reviews import (
    ExamReviewResponse,
    QuestionReview,
    StudentAnswerReview,
    CriterionScore,
    AISuggestion
)
from src.domain.requests.reviews import (
    AcceptSuggestionRequest,
    RejectSuggestionRequest,
    AdjustGradeRequest,
    FinalizeReviewRequest
)

from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.student_repository_interface import StudentRepositoryInterface
from src.interfaces.repositories.grading_criteria_repository_interface import GradingCriteriaRepositoryInterface
from src.interfaces.repositories.exam_criteria_repository_interface import ExamCriteriaRepositoryInterface
from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface

from src.models.entities.student_answer_criteria_scores import StudentAnswerCriteriaScore
from src.models.entities.student_answers import StudentAnswer

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError
from src.errors.domain.validate_error import ValidateError
from src.core.logging_config import get_logger


logger = get_logger(__name__)


class ReviewService(ReviewServiceInterface):
    """Implementação do serviço de revisão."""
    
    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface,
        exam_question_repository: ExamQuestionRepositoryInterface,
        student_repository: StudentRepositoryInterface,
        grading_criteria_repository: GradingCriteriaRepositoryInterface,
        exam_criteria_repository: ExamCriteriaRepositoryInterface,
        class_repository: ClassesRepositoryInterface
    ):
        self.__exam_repository = exam_repository
        self.__student_answer_repository = student_answer_repository
        self.__exam_question_repository = exam_question_repository
        self.__student_repository = student_repository
        self.__grading_criteria_repository = grading_criteria_repository
        self.__exam_criteria_repository = exam_criteria_repository
        self.__class_repository = class_repository
    
    def get_exam_review(self, db: Session, exam_uuid: UUID, user_uuid: UUID) -> ExamReviewResponse:
        """Retorna dados completos para revisão de uma prova."""
        
        # Buscar prova
        exam = self.__exam_repository.get_by_uuid(db, exam_uuid)
        if not exam:
            raise NotFoundError(f"Prova {exam_uuid} não encontrada")
        
        # Validar se usuário é dono da prova
        if str(exam.created_by) != str(user_uuid):
            raise UnauthorizedError("Você não tem permissão para revisar esta prova")
        
        # Buscar nome da turma
        class_name = None
        if exam.class_uuid:
            try:
                class_entity = self.__class_repository.get_by_uuid(db, exam.class_uuid)
                class_name = class_entity.name if class_entity else None
            except Exception:
                logger.warning("Não foi possível buscar nome da turma: %s", exam.class_uuid)
        
        # Buscar critérios da prova
        exam_criteria_list = self.__exam_criteria_repository.get_by_exam(db, exam_uuid)
        
        grading_criteria = []
        for ec in exam_criteria_list:
            try:
                criteria = self.__grading_criteria_repository.get_by_uuid(db, ec.criteria_uuid)
                grading_criteria.append(
                    CriterionScore(
                        criterion_uuid=ec.criteria_uuid,
                        criterion_name=criteria.name,
                        criterion_description=criteria.description,
                        max_score=float(ec.max_points),
                        weight=float(ec.weight),
                        raw_score=0.0,  # Placeholder
                        weighted_score=None,
                        feedback=None
                    )
                )
            except Exception as e:
                logger.warning("Erro ao buscar critério %s: %s", ec.criteria_uuid, str(e))
        
        # Buscar questões da prova
        questions = self.__exam_question_repository.get_by_exam(db, exam_uuid)
        if not questions:
            raise NotFoundError("Nenhuma questão encontrada para esta prova")
        
        # Montar questões com respostas dos alunos
        questions_review = []
        total_students_set = set()
        
        for idx, question in enumerate(questions, 1):
            # Buscar todas as respostas para esta questão
            answers = db.query(StudentAnswer).filter(
                StudentAnswer.question_uuid == question.uuid,
                StudentAnswer.exam_uuid == exam_uuid
            ).all()
            
            student_answers_review = []
            
            for answer in answers:
                total_students_set.add(str(answer.student_uuid))
                
                # Buscar dados do aluno
                try:
                    student = self.__student_repository.get_by_uuid(db, answer.student_uuid)
                    student_name = student.full_name if student else "Aluno Desconhecido"
                    student_email = student.email if student else None
                except Exception:
                    student_name = "Aluno Desconhecido"
                    student_email = None
                    logger.warning("Não foi possível buscar aluno: %s", answer.student_uuid)
                
                # Buscar scores por critério
                criteria_scores_entities = db.query(StudentAnswerCriteriaScore).filter(
                    StudentAnswerCriteriaScore.student_answer_uuid == answer.uuid
                ).all()
                
                criteria_scores = []
                for score_entity in criteria_scores_entities:
                    try:
                        criteria = self.__grading_criteria_repository.get_by_uuid(db, score_entity.criteria_uuid)
                        criterion_name = criteria.name
                        criterion_description = criteria.description
                    except Exception:
                        criterion_name = "Critério"
                        criterion_description = None
                        logger.warning("Não foi possível buscar critério: %s", score_entity.criteria_uuid)
                    
                    # Buscar configuração do critério na prova
                    criterion_config = next(
                        (ec for ec in exam_criteria_list if ec.criteria_uuid == score_entity.criteria_uuid),
                        None
                    )
                    max_score = float(criterion_config.max_points) if criterion_config and criterion_config.max_points else 10.0
                    weight = float(criterion_config.weight) if criterion_config and criterion_config.weight else 1.0
                    
                    criteria_scores.append(
                        CriterionScore(
                            criterion_uuid=score_entity.criteria_uuid,
                            criterion_name=criterion_name,
                            criterion_description=criterion_description,
                            max_score=max_score,
                            weight=weight,
                            raw_score=float(score_entity.raw_score),
                            weighted_score=float(score_entity.weighted_score) if score_entity.weighted_score else None,
                            feedback=score_entity.feedback
                        )
                    )
                
                # Gerar sugestões mockadas da IA (enquanto não temos persistência)
                ai_suggestions = self._generate_mock_suggestions(answer)
                
                student_answers_review.append(
                    StudentAnswerReview(
                        answer_uuid=answer.uuid,
                        student_uuid=answer.student_uuid,
                        student_name=student_name,
                        student_email=student_email,
                        answer_text=answer.answer or "",
                        score=float(answer.score) if answer.score is not None else None,
                        status=answer.status,
                        feedback=answer.feedback,
                        criteria_scores=criteria_scores,
                        ai_suggestions=ai_suggestions,
                        graded_at=answer.graded_at
                    )
                )
            
            # Usar pontuação da questão (não somar critérios)
            # A pontuação da questão é definida em exam_questions.points
            question_max_score = float(question.points) if question.points else 10.0
            
            questions_review.append(
                QuestionReview(
                    question_uuid=question.uuid,
                    question_number=idx,
                    statement=question.statement,
                    expected_answer=None,  # Campo não existe na tabela exam_questions
                    max_score=question_max_score,
                    student_answers=student_answers_review
                )
            )
        
        # Buscar data de correção (mais recente)
        graded_at = None
        all_answers = db.query(StudentAnswer).filter(
            StudentAnswer.exam_uuid == exam_uuid,
            StudentAnswer.is_graded.is_(True)
        ).all()
        
        if all_answers:
            graded_dates = [a.graded_at for a in all_answers if a.graded_at]
            graded_at = max(graded_dates) if graded_dates else None
        
        return ExamReviewResponse(
            exam_uuid=exam_uuid,
            exam_title=exam.title,
            exam_description=exam.description,
            class_name=class_name,
            status=exam.status,
            total_students=len(total_students_set),
            total_questions=len(questions),
            graded_at=graded_at,
            questions=questions_review,
            grading_criteria=grading_criteria
        )
    
    def _generate_mock_suggestions(self, answer: StudentAnswer) -> List[AISuggestion]:
        """Gera sugestões mockadas da IA (temporário)."""
        
        # TODO: Substituir por dados reais quando houver persistência de sugestões da IA
        if answer.feedback and len(answer.feedback) > 50:
            return [
                AISuggestion(
                    suggestion_id=f"sug_{answer.uuid}_1",
                    type="feedback",
                    content="Considere adicionar mais detalhes sobre o conceito X",
                    confidence=0.75,
                    reasoning="A resposta aborda parcialmente o tema mas falta aprofundamento",
                    accepted=False
                )
            ]
        return []
    
    def accept_suggestion(
        self,
        db: Session,
        request: AcceptSuggestionRequest,
        user_uuid: UUID
    ) -> dict:
        """Aceita uma sugestão da IA."""
        
        # Buscar resposta
        answer = self.__student_answer_repository.get_by_uuid(db, request.answer_uuid)
        if not answer:
            raise NotFoundError(f"Resposta {request.answer_uuid} não encontrada")
        
        # Buscar prova para validar permissão
        exam = self.__exam_repository.get_by_uuid(db, answer.exam_uuid)
        if not exam:
            raise NotFoundError("Prova não encontrada")
        
        if str(exam.teacher_uuid) != str(user_uuid):
            raise UnauthorizedError("Você não tem permissão para modificar esta correção")
        
        # TODO: Implementar lógica de aceitar sugestão quando houver persistência
        # Por ora, apenas retornamos sucesso
        logger.info(
            "Sugestão %s aceita para resposta %s pelo usuário %s",
            request.suggestion_id,
            request.answer_uuid,
            user_uuid
        )
        
        return {
            "message": "Sugestão aceita com sucesso",
            "suggestion_id": request.suggestion_id,
            "answer_uuid": str(request.answer_uuid)
        }
    
    def reject_suggestion(
        self,
        db: Session,
        request: RejectSuggestionRequest,
        user_uuid: UUID
    ) -> dict:
        """Rejeita uma sugestão da IA."""
        
        # Buscar resposta
        answer = self.__student_answer_repository.get_by_uuid(db, request.answer_uuid)
        if not answer:
            raise NotFoundError(f"Resposta {request.answer_uuid} não encontrada")
        
        # Buscar prova para validar permissão
        exam = self.__exam_repository.get_by_uuid(db, answer.exam_uuid)
        if not exam:
            raise NotFoundError("Prova não encontrada")
        
        if str(exam.teacher_uuid) != str(user_uuid):
            raise UnauthorizedError("Você não tem permissão para modificar esta correção")
        
        # TODO: Implementar lógica de rejeitar sugestão quando houver persistência
        logger.info(
            "Sugestão %s rejeitada para resposta %s pelo usuário %s. Motivo: %s",
            request.suggestion_id,
            request.answer_uuid,
            user_uuid,
            request.reason or "Não especificado"
        )
        
        return {
            "message": "Sugestão rejeitada com sucesso",
            "suggestion_id": request.suggestion_id,
            "answer_uuid": str(request.answer_uuid)
        }
    
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
        
        if str(exam.teacher_uuid) != str(user_uuid):
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
        answer.graded_at = db.execute(db.query(StudentAnswer).filter(StudentAnswer.uuid == answer.uuid)).scalar_one().updated_at
        
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
                    # Recalcular weighted_score se houver peso
                    # TODO: Buscar peso do exam_criteria para recalcular
        
        db.commit()
        db.refresh(answer)
        
        logger.info(
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
    
    def finalize_review(
        self,
        db: Session,
        request: FinalizeReviewRequest,
        user_uuid: UUID
    ) -> dict:
        """Finaliza revisão e gera relatório."""
        
        # Buscar prova
        exam = self.__exam_repository.get_by_uuid(db, request.exam_uuid)
        if not exam:
            raise NotFoundError(f"Prova {request.exam_uuid} não encontrada")
        
        if str(exam.teacher_uuid) != str(user_uuid):
            raise UnauthorizedError("Você não tem permissão para finalizar esta revisão")
        
        # TODO: Implementar geração de PDF
        pdf_url = None
        if request.generate_pdf:
            logger.info("Solicitação de geração de PDF para prova %s", request.exam_uuid)
            # pdf_url = gerar_relatorio_pdf(exam_uuid)
        
        # TODO: Implementar envio de notificações
        if request.send_notifications:
            logger.info("Solicitação de envio de notificações para prova %s", request.exam_uuid)
            # enviar_notificacoes_alunos(exam_uuid)
        
        # Atualizar status da prova para FINISHED (se aplicável)
        # exam.status = "FINISHED"
        # db.commit()
        
        logger.info(
            "Revisão finalizada para prova %s pelo usuário %s",
            request.exam_uuid,
            user_uuid
        )
        
        return {
            "message": "Revisão finalizada com sucesso",
            "exam_uuid": str(request.exam_uuid),
            "pdf_url": pdf_url,
            "notifications_sent": request.send_notifications
        }
