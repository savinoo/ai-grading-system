"""
Serviço para estatísticas do dashboard do professor.
"""

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from src.interfaces.services.dashboard.dashboard_service_interface import DashboardServiceInterface
from src.domain.responses.dashboard.dashboard_stats_response import (
    DashboardStatsResponse,
    ExamStatsCount,
    AnswerStatsCount,
    RecentExam,
    PendingAction
)

from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface
from src.interfaces.repositories.class_student_repository_interface import ClassStudentRepositoryInterface

from src.models.entities.exams import Exams
from src.models.entities.student_answers import StudentAnswer
from src.models.entities.exam_questions import ExamQuestion
from src.models.entities.class_student import ClassStudent

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class DashboardService(DashboardServiceInterface):
    """Implementação do serviço de dashboard."""
    
    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface,
        exam_question_repository: ExamQuestionRepositoryInterface,
        class_repository: ClassesRepositoryInterface,
        class_student_repository: ClassStudentRepositoryInterface
    ):
        self.__exam_repository = exam_repository
        self.__student_answer_repository = student_answer_repository
        self.__exam_question_repository = exam_question_repository
        self.__class_repository = class_repository
        self.__class_student_repository = class_student_repository
    
    def get_teacher_dashboard_stats(
        self,
        db: Session,
        teacher_uuid: UUID,
        limit_recent_exams: int = 10
    ) -> DashboardStatsResponse:
        """
        Obtém estatísticas do dashboard para um professor.
        """
        logger.info("Buscando estatísticas do dashboard para professor: %s", teacher_uuid)
        
        # 1. Contar provas por status
        exam_stats = self._get_exam_stats(db, teacher_uuid)
        
        # 2. Contar respostas
        answer_stats = self._get_answer_stats(db, teacher_uuid)
        
        # 3. Buscar provas recentes com progresso
        recent_exams = self._get_recent_exams(db, teacher_uuid, limit_recent_exams)
        
        # 4. Buscar ações pendentes
        pending_actions = self._get_pending_actions(db, teacher_uuid)
        
        return DashboardStatsResponse(
            exam_stats=exam_stats,
            answer_stats=answer_stats,
            recent_exams=recent_exams,
            pending_actions=pending_actions
        )
    
    def _get_exam_stats(self, db: Session, teacher_uuid: UUID) -> ExamStatsCount:
        """Conta provas por status."""
        base_query = db.query(Exams).filter(
            Exams.created_by == teacher_uuid,
            Exams.active.is_(True)
        )
        
        draft = base_query.filter(Exams.status == "DRAFT").count()
        active = base_query.filter(Exams.status == "ACTIVE").count()
        grading = base_query.filter(Exams.status == "GRADING").count()
        graded = base_query.filter(Exams.status == "GRADED").count()
        finalized = base_query.filter(Exams.status == "FINALIZED").count()
        total = base_query.count()
        
        return ExamStatsCount(
            draft=draft,
            active=active,
            grading=grading,
            graded=graded,
            finalized=finalized,
            total=total
        )
    
    def _get_answer_stats(self, db: Session, teacher_uuid: UUID) -> AnswerStatsCount:
        """Conta respostas por status."""
        # Buscar apenas respostas de provas do professor
        base_query = db.query(StudentAnswer).join(
            Exams,
            StudentAnswer.exam_uuid == Exams.uuid
        ).filter(
            Exams.created_by == teacher_uuid,
            Exams.active.is_(True)
        )
        
        total = base_query.count()
        
        # Respostas não corrigidas (is_graded = False ou NULL)
        pending = base_query.filter(
            or_(
                StudentAnswer.is_graded.is_(False),
                StudentAnswer.is_graded.is_(None)
            )
        ).count()
        
        # Respostas corrigidas
        graded = base_query.filter(
            StudentAnswer.is_graded.is_(True)
        ).count()
        
        # Respostas aguardando revisão (status GRADED mas não finalized)
        pending_review = base_query.filter(
            StudentAnswer.status == "GRADED",
            Exams.status != "FINALIZED"
        ).count()
        
        return AnswerStatsCount(
            total=total,
            pending=pending,
            graded=graded,
            pending_review=pending_review
        )
    
    def _get_recent_exams(
        self,
        db: Session,
        teacher_uuid: UUID,
        limit: int
    ) -> List[RecentExam]:
        """Busca provas recentes com estatísticas de progresso."""
        # Buscar provas ordenadas por data de criação (mais recentes primeiro)
        exams = db.query(Exams).filter(
            Exams.created_by == teacher_uuid,
            Exams.active.is_(True)
        ).order_by(Exams.created_at.desc()).limit(limit).all()
        
        result = []
        
        for exam in exams:
            # Buscar turma
            class_name = None
            total_students = 0
            
            if exam.class_uuid:
                try:
                    class_obj = self.__class_repository.get_by_uuid(db, exam.class_uuid)
                    class_name = class_obj.name if class_obj else None
                    # Contar alunos na turma
                    total_students = db.query(ClassStudent).filter(
                        ClassStudent.class_uuid == exam.class_uuid,
                        ClassStudent.active.is_(True)
                    ).count()
                except Exception:
                    logger.warning("Não foi possível buscar turma: %s", exam.class_uuid)
            
            # Contar questões
            total_questions = db.query(ExamQuestion).filter(
                ExamQuestion.exam_uuid == exam.uuid,
                ExamQuestion.active.is_(True)
            ).count()
            
            # Contar respostas
            answers_submitted = db.query(StudentAnswer).filter(
                StudentAnswer.exam_uuid == exam.uuid
            ).count()
            
            answers_graded = db.query(StudentAnswer).filter(
                StudentAnswer.exam_uuid == exam.uuid,
                StudentAnswer.is_graded.is_(True)
            ).count()
            
            pending_review = db.query(StudentAnswer).filter(
                StudentAnswer.exam_uuid == exam.uuid,
                StudentAnswer.status == "GRADED"
            ).count()
            
            result.append(
                RecentExam(
                    uuid=exam.uuid,
                    title=exam.title,
                    class_name=class_name,
                    status=exam.status,
                    starts_at=exam.starts_at,
                    ends_at=exam.ends_at,
                    total_questions=total_questions,
                    total_students=total_students,
                    answers_submitted=answers_submitted,
                    answers_graded=answers_graded,
                    pending_review=pending_review,
                    created_at=exam.created_at
                )
            )
        
        return result
    
    def _get_pending_actions(
        self,
        db: Session,
        teacher_uuid: UUID
    ) -> List[PendingAction]:
        """Identifica ações pendentes para o professor."""
        actions = []
        
        # 1. Provas em rascunho (alta prioridade se criadas há mais de 7 dias)
        draft_exams = db.query(Exams).filter(
            Exams.created_by == teacher_uuid,
            Exams.status == "DRAFT",
            Exams.active.is_(True)
        ).all()
        
        for exam in draft_exams:
            actions.append(
                PendingAction(
                    type="draft",
                    exam_uuid=exam.uuid,
                    exam_title=exam.title,
                    description=f"Finalizar rascunho da prova '{exam.title}'",
                    count=1,
                    priority="normal",
                    created_at=exam.created_at
                )
            )
        
        # 2. Provas com respostas aguardando revisão (alta prioridade)
        graded_exams = db.query(
            Exams.uuid,
            Exams.title,
            Exams.created_at,
            func.count(StudentAnswer.uuid).label('pending_count')  # pylint: disable=not-callable
        ).join(
            StudentAnswer,
            StudentAnswer.exam_uuid == Exams.uuid
        ).filter(
            Exams.created_by == teacher_uuid,
            Exams.status != "FINALIZED",
            StudentAnswer.status == "GRADED"
        ).group_by(Exams.uuid, Exams.title, Exams.created_at).all()
        
        for exam_uuid, exam_title, created_at, count in graded_exams:
            if count > 0:
                actions.append(
                    PendingAction(
                        type="review",
                        exam_uuid=exam_uuid,
                        exam_title=exam_title,
                        description=f"Revisar {count} resposta(s) corrigida(s) pela IA",
                        count=count,
                        priority="high",
                        created_at=created_at
                    )
                )
        
        # 3. Provas ativas com respostas não corrigidas
        pending_grading = db.query(
            Exams.uuid,
            Exams.title,
            Exams.created_at,
            func.count(StudentAnswer.uuid).label('pending_count')  # pylint: disable=not-callable
        ).join(
            StudentAnswer,
            StudentAnswer.exam_uuid == Exams.uuid
        ).filter(
            Exams.created_by == teacher_uuid,
            Exams.status.in_(["ACTIVE", "GRADING"]),
            or_(
                StudentAnswer.is_graded.is_(False),
                StudentAnswer.is_graded.is_(None)
            )
        ).group_by(Exams.uuid, Exams.title, Exams.created_at).all()
        
        for exam_uuid, exam_title, created_at, count in pending_grading:
            if count > 0:
                actions.append(
                    PendingAction(
                        type="grading",
                        exam_uuid=exam_uuid,
                        exam_title=exam_title,
                        description=f"Corrigir {count} resposta(s) pendente(s)",
                        count=count,
                        priority="normal",
                        created_at=created_at
                    )
                )
        
        # Ordenar por prioridade e data
        priority_order = {"high": 0, "normal": 1, "low": 2}
        actions.sort(key=lambda x: (priority_order.get(x.priority, 1), x.created_at))
        
        return actions[:10]  # Limitar a 10 ações mais importantes
