"""
Serviço para estatísticas do dashboard do professor.
"""

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

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
from src.interfaces.repositories.class_student_repository_interface import ClassStudentRepositoryInterface

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class DashboardService(DashboardServiceInterface):
    """Implementação do serviço de dashboard."""
    
    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface,
        exam_question_repository: ExamQuestionRepositoryInterface,
        class_student_repository: ClassStudentRepositoryInterface
    ):
        self.__exam_repository = exam_repository
        self.__student_answer_repository = student_answer_repository
        self.__exam_question_repository = exam_question_repository
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
        exam_stats = self.__get_exam_stats(db, teacher_uuid)
        
        # 2. Contar respostas
        answer_stats = self._get_answer_stats(db, teacher_uuid)
        
        # 3. Buscar provas recentes com progresso
        recent_exams = self._get_recent_exams(db, teacher_uuid, limit_recent_exams)
        
        # 4. Buscar ações pendentes
        pending_actions = self.__get_pending_actions(db, teacher_uuid)
        
        return DashboardStatsResponse(
            exam_stats=exam_stats,
            answer_stats=answer_stats,
            recent_exams=recent_exams,
            pending_actions=pending_actions
        )
    
    def __get_exam_stats(self, db: Session, teacher_uuid: UUID) -> ExamStatsCount:
        """Conta provas por status."""
        draft = self.__exam_repository.count_by_teacher_and_status(db, teacher_uuid, "DRAFT")
        active = self.__exam_repository.count_by_teacher_and_status(db, teacher_uuid, "ACTIVE")
        grading = self.__exam_repository.count_by_teacher_and_status(db, teacher_uuid, "GRADING")
        graded = self.__exam_repository.count_by_teacher_and_status(db, teacher_uuid, "GRADED")
        finalized = self.__exam_repository.count_by_teacher_and_status(db, teacher_uuid, "FINALIZED")
        total = self.__exam_repository.count_by_teacher(db, teacher_uuid)
        
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
        total = self.__student_answer_repository.count_by_teacher(db, teacher_uuid)
        
        # Respostas não corrigidas (is_graded = False)
        pending = self.__student_answer_repository.count_by_teacher_and_graded(db, teacher_uuid, False)
        
        # Respostas corrigidas
        graded = self.__student_answer_repository.count_by_teacher_and_graded(db, teacher_uuid, True)
        
        # Respostas aguardando revisão (status GRADED)
        pending_review = self.__student_answer_repository.count_by_teacher_and_status(
            db, teacher_uuid, "GRADED"
        )
        
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
        exams = self.__exam_repository.get_by_teacher(
            db,
            teacher_uuid,
            limit=limit,
            active_only=True
        )
        
        result = []
        
        for exam in exams:
            # Buscar turma (class_name já vem populado do repositório)
            class_name = getattr(exam, 'class_name', None)
            total_students = 0
            
            if exam.class_uuid:
                try:
                    # Contar alunos na turma
                    total_students = self.__class_student_repository.count_students_in_class(
                        db,
                        exam.class_uuid,
                        active_only=True
                    )
                except Exception:
                    logger.warning("Não foi possível contar alunos da turma: %s", exam.class_uuid)
            
            # Contar questões
            total_questions = self.__exam_question_repository.count_by_exam(
                db,
                exam.uuid,
                active_only=True
            )
            
            # Contar respostas
            answers_submitted = self.__student_answer_repository.count_by_exam(db, exam.uuid)
            
            answers_graded = self.__student_answer_repository.count_by_exam_and_graded(
                db,
                exam.uuid,
                is_graded=True
            )
            
            pending_review = self.__student_answer_repository.count_by_exam_and_status(
                db,
                exam.uuid,
                status="GRADED"
            )
            
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
    
    def __get_pending_actions(
        self,
        db: Session,
        teacher_uuid: UUID
    ) -> List[PendingAction]:
        """Identifica ações pendentes para o professor."""
        actions = []
        
        # 1. Provas em rascunho
        draft_exams = self.__exam_repository.get_by_teacher(
            db,
            teacher_uuid,
            limit=100,
            active_only=True
        )
        
        for exam in draft_exams:
            if exam.status == "DRAFT":
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
        exams_not_finalized = [e for e in draft_exams if e.status != "FINALIZED"]
        
        for exam in exams_not_finalized:
            count = self.__student_answer_repository.count_by_exam_and_status(
                db,
                exam.uuid,
                status="GRADED"
            )
            if count > 0:
                actions.append(
                    PendingAction(
                        type="review",
                        exam_uuid=exam.uuid,
                        exam_title=exam.title,
                        description=f"Revisar {count} resposta(s) corrigida(s) pela IA",
                        count=count,
                        priority="high",
                        created_at=exam.created_at
                    )
                )
        
        # 3. Provas ativas com respostas não corrigidas
        active_exams = [e for e in draft_exams if e.status in ["ACTIVE", "GRADING"]]
        
        for exam in active_exams:
            count = self.__student_answer_repository.count_by_exam_and_graded(
                db,
                exam.uuid,
                is_graded=False
            )
            if count > 0:
                actions.append(
                    PendingAction(
                        type="grading",
                        exam_uuid=exam.uuid,
                        exam_title=exam.title,
                        description=f"Corrigir {count} resposta(s) pendente(s)",
                        count=count,
                        priority="normal",
                        created_at=exam.created_at
                    )
                )
        
        # Ordenar por prioridade e data
        priority_order = {"high": 0, "normal": 1, "low": 2}
        actions.sort(key=lambda x: (priority_order.get(x.priority, 1), x.created_at))
        
        return actions[:10]
