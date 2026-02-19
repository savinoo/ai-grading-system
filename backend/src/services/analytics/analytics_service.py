"""
Serviço de análise pedagógica.

Processa resultados das correções para gerar insights sobre:
- Desempenho individual do aluno (tendência, gaps, pontos fortes)
- Desempenho agregado da turma (outliers, distribuição, gaps comuns)
"""

import statistics
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from src.domain.responses.analytics import (
    ClassAnalyticsResponse,
    ClassAnalyticsSummaryResponse,
    ClassStudentSummaryResponse,
    GradeDistributionResponse,
    LearningGapResponse,
    StrengthResponse,
    StudentPerformanceResponse,
    SubmissionSummaryResponse,
)
from src.errors.domain.not_found import NotFoundError
from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface
from src.interfaces.repositories.student_repository_interface import StudentRepositoryInterface
from src.interfaces.services.analytics.analytics_service_interface import AnalyticsServiceInterface
from src.models.entities.class_student import ClassStudent
from src.models.entities.exams import Exams
from src.models.entities.grading_criteria import GradingCriteria
from src.models.entities.student import Student
from src.models.entities.student_answer_criteria_scores import StudentAnswerCriteriaScore
from src.models.entities.student_answers import StudentAnswer

from src.core.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Constantes de limiar pedagógico
# ---------------------------------------------------------------------------

_GAP_THRESHOLD = 6.0          # Média abaixo disso → gap de aprendizado
_STRENGTH_THRESHOLD = 8.0     # Média acima disso → ponto forte
_TREND_MIN_SAMPLES = 3        # Mínimo de submissões para calcular tendência


class AnalyticsService(AnalyticsServiceInterface):
    """Implementação do serviço de análise pedagógica."""

    def __init__(
        self,
        classes_repository: ClassesRepositoryInterface,
        student_repository: StudentRepositoryInterface,
    ) -> None:
        self.__classes_repo = classes_repository
        self.__student_repo = student_repository

    # =======================================================================
    # Público
    # =======================================================================

    def get_class_analytics(
        self,
        db: Session,
        class_uuid: UUID,
        teacher_uuid: UUID,
    ) -> ClassAnalyticsResponse:
        """Retorna análise pedagógica completa de uma turma."""
        logger.info("Calculando analytics para turma %s", class_uuid)

        try:
            turma = self.__classes_repo.get_by_uuid(db, class_uuid)
        except NoResultFound as e:
            raise NotFoundError(f"Turma {class_uuid} não encontrada") from e

        # Buscar alunos da turma
        class_students = self._get_class_students(db, class_uuid)
        student_uuids = [str(cs.student_uuid) for cs in class_students]

        if not student_uuids:
            return self._empty_class_analytics(class_uuid, turma.name)

        # Buscar provas da turma
        exams = self._get_class_exams(db, class_uuid)
        exam_uuids = [str(e.uuid) for e in exams]

        # Buscar respostas corrigidas das provas da turma
        all_answers = self._get_graded_answers_for_exams(db, exam_uuids)

        if not all_answers:
            return self._empty_class_analytics(class_uuid, turma.name)

        # Mapear título de prova
        exam_titles: Dict[str, str] = {str(e.uuid): e.title for e in exams}

        # Construir perfil de cada aluno
        students_map: Dict[str, Student] = self._load_students_map(db, student_uuids)
        criteria_scores_map = self._load_criteria_scores(db, [str(a.uuid) for a in all_answers])

        student_profiles: List[StudentPerformanceResponse] = []
        for student_uuid in student_uuids:
            student = students_map.get(student_uuid)
            if not student:
                continue
            student_answers = [a for a in all_answers if str(a.student_uuid) == student_uuid]
            profile = self._build_student_profile(
                student, student_answers, criteria_scores_map, exam_titles
            )
            student_profiles.append(profile)

        return self._aggregate_class_analytics(class_uuid, turma.name, student_profiles)

    def list_classes_analytics(
        self,
        db: Session,
        teacher_uuid: UUID,
    ) -> List[ClassAnalyticsSummaryResponse]:
        """Retorna sumário analítico de todas as turmas do professor."""
        logger.info("Listando analytics das turmas do professor %s", teacher_uuid)

        stmt = select(Exams.class_uuid).where(
            Exams.created_by == str(teacher_uuid),
            Exams.active.is_(True),
            Exams.class_uuid.isnot(None),
        ).distinct()
        class_uuids_rows = db.execute(stmt).fetchall()
        class_uuids = [row[0] for row in class_uuids_rows]

        summaries: List[ClassAnalyticsSummaryResponse] = []
        for class_uuid in class_uuids:
            try:
                analytics = self.get_class_analytics(
                    db, UUID(str(class_uuid)), teacher_uuid
                )
                summaries.append(
                    ClassAnalyticsSummaryResponse(
                        class_uuid=analytics.class_uuid,
                        class_name=analytics.class_name,
                        total_students=analytics.total_students,
                        total_submissions=analytics.total_submissions,
                        class_avg_score=analytics.class_avg_score,
                        struggling_count=len(analytics.struggling_students),
                        top_performers_count=len(analytics.top_performers),
                        analysis_timestamp=analytics.analysis_timestamp,
                    )
                )
            except Exception as e:  # pylint: disable=broad-except
                logger.warning("Erro ao calcular analytics da turma %s: %s", class_uuid, e)

        summaries.sort(key=lambda s: s.struggling_count, reverse=True)
        return summaries

    def get_student_performance(
        self,
        db: Session,
        student_uuid: UUID,
        class_uuid: UUID,
        teacher_uuid: UUID,
    ) -> StudentPerformanceResponse:
        """Retorna perfil de desempenho individual de um aluno em uma turma."""
        logger.info("Calculando performance do aluno %s na turma %s", student_uuid, class_uuid)

        try:
            student = self.__student_repo.get_by_uuid(db, student_uuid)
        except NoResultFound as e:
            raise NotFoundError(f"Aluno {student_uuid} não encontrado") from e

        exams = self._get_class_exams(db, class_uuid)
        exam_uuids = [str(e.uuid) for e in exams]
        exam_titles = {str(e.uuid): e.title for e in exams}

        # Respostas corrigidas do aluno nas provas da turma
        stmt = select(StudentAnswer).where(
            StudentAnswer.student_uuid == str(student_uuid),
            StudentAnswer.exam_uuid.in_(exam_uuids),
            StudentAnswer.is_graded.is_(True),
        ).order_by(StudentAnswer.graded_at)
        student_answers: List[StudentAnswer] = list(db.execute(stmt).scalars().all())

        criteria_scores_map = self._load_criteria_scores(db, [str(a.uuid) for a in student_answers])

        return self._build_student_profile(
            student, student_answers, criteria_scores_map, exam_titles
        )

    # =======================================================================
    # Helpers de banco de dados
    # =======================================================================

    def _get_class_students(self, db: Session, class_uuid: UUID) -> Sequence[ClassStudent]:
        stmt = select(ClassStudent).where(
            ClassStudent.class_uuid == str(class_uuid),
            ClassStudent.active.is_(True),
        )
        return db.execute(stmt).scalars().all()

    def _get_class_exams(self, db: Session, class_uuid: UUID) -> Sequence[Exams]:
        stmt = select(Exams).where(
            Exams.class_uuid == str(class_uuid),
            Exams.active.is_(True),
        )
        return db.execute(stmt).scalars().all()

    def _get_graded_answers_for_exams(
        self, db: Session, exam_uuids: List[str]
    ) -> Sequence[StudentAnswer]:
        if not exam_uuids:
            return []
        stmt = select(StudentAnswer).where(
            StudentAnswer.exam_uuid.in_(exam_uuids),
            StudentAnswer.is_graded.is_(True),
        ).order_by(StudentAnswer.student_uuid, StudentAnswer.graded_at)
        return db.execute(stmt).scalars().all()

    def _load_students_map(self, db: Session, student_uuids: List[str]) -> Dict[str, Student]:
        stmt = select(Student).where(Student.uuid.in_(student_uuids))
        students = db.execute(stmt).scalars().all()
        return {str(s.uuid): s for s in students}

    def _load_criteria_scores(
        self, db: Session, answer_uuids: List[str]
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Retorna mapa de answer_uuid -> [(criterion_name, raw_score), ...].
        Inclui join com GradingCriteria para recuperar o nome do critério.
        """
        if not answer_uuids:
            return {}

        stmt = (
            select(
                StudentAnswerCriteriaScore.student_answer_uuid,
                GradingCriteria.name,
                StudentAnswerCriteriaScore.raw_score,
            )
            .join(
                GradingCriteria,
                StudentAnswerCriteriaScore.criteria_uuid == GradingCriteria.uuid,
            )
            .where(StudentAnswerCriteriaScore.student_answer_uuid.in_(answer_uuids))
        )
        rows = db.execute(stmt).fetchall()

        mapping: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        for answer_uuid, criterion_name, raw_score in rows:
            mapping[str(answer_uuid)].append((criterion_name, float(raw_score)))
        return dict(mapping)

    # =======================================================================
    # Lógica analítica
    # =======================================================================

    def _build_student_profile(
        self,
        student: Student,
        answers: List[StudentAnswer],
        criteria_scores_map: Dict[str, List[Tuple[str, float]]],
        exam_titles: Dict[str, str],
    ) -> StudentPerformanceResponse:
        """Constrói o perfil analítico completo de um aluno."""
        if not answers:
            return StudentPerformanceResponse(
                student_uuid=UUID(str(student.uuid)),
                student_name=student.full_name,
                student_email=getattr(student, "email", None),
            )

        # Histórico de submissões
        history: List[SubmissionSummaryResponse] = []
        scores: List[float] = []
        criterion_tracker: Dict[str, List[float]] = defaultdict(list)

        for answer in answers:
            score = float(answer.score) if answer.score is not None else 0.0
            scores.append(score)

            history.append(
                SubmissionSummaryResponse(
                    answer_uuid=UUID(str(answer.uuid)),
                    question_uuid=UUID(str(answer.question_uuid)),
                    exam_uuid=UUID(str(answer.exam_uuid)),
                    exam_title=exam_titles.get(str(answer.exam_uuid), ""),
                    score=score,
                    max_score=10.0,  # padrão; idealmente viria da questão
                    graded_at=answer.graded_at,
                )
            )

            for criterion_name, raw_score in criteria_scores_map.get(str(answer.uuid), []):
                criterion_tracker[criterion_name].append(raw_score)

        avg_score = statistics.mean(scores) if scores else 0.0
        trend, trend_confidence = self._detect_trend(scores)
        learning_gaps = self._identify_gaps(criterion_tracker)
        strengths = self._identify_strengths(criterion_tracker)

        first_graded = min((a.graded_at for a in answers if a.graded_at), default=None)
        last_graded = max((a.graded_at for a in answers if a.graded_at), default=None)

        return StudentPerformanceResponse(
            student_uuid=UUID(str(student.uuid)),
            student_name=student.full_name,
            student_email=getattr(student, "email", None),
            avg_score=avg_score,
            submission_count=len(answers),
            trend=trend,
            trend_confidence=trend_confidence,
            learning_gaps=learning_gaps,
            strengths=strengths,
            submissions_history=history,
            first_submission=first_graded,
            last_submission=last_graded,
        )

    def _detect_trend(self, scores: List[float]) -> Tuple[str, float]:
        """Regressão linear simples nas notas ao longo do tempo."""
        if len(scores) < _TREND_MIN_SAMPLES:
            return "insufficient_data", 0.0

        x = np.arange(len(scores), dtype=float)
        y = np.array(scores, dtype=float)

        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        y_pred = np.polyval(coeffs, x)
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        confidence = max(0.0, min(1.0, r_squared))

        if abs(slope) < 0.1:
            return "stable", confidence
        if slope > 0:
            return "improving", confidence
        return "declining", confidence

    def _identify_gaps(
        self, criterion_tracker: Dict[str, List[float]]
    ) -> List[LearningGapResponse]:
        """Detecta critérios onde o aluno consistentemente vai mal."""
        gaps: List[LearningGapResponse] = []

        for criterion_name, scores in criterion_tracker.items():
            avg = statistics.mean(scores)
            if avg < _GAP_THRESHOLD:
                if avg < 4.0:
                    severity = "high"
                elif avg < 5.5:
                    severity = "medium"
                else:
                    severity = "low"

                gaps.append(
                    LearningGapResponse(
                        criterion_name=criterion_name,
                        severity=severity,
                        evidence_count=len(scores),
                        avg_score=round(avg, 2),
                        suggestion=self._gap_suggestion(criterion_name),
                    )
                )

        return sorted(gaps, key=lambda g: g.avg_score)

    def _identify_strengths(
        self, criterion_tracker: Dict[str, List[float]]
    ) -> List[StrengthResponse]:
        """Detecta critérios onde o aluno se destaca consistentemente."""
        strengths: List[StrengthResponse] = []

        for criterion_name, scores in criterion_tracker.items():
            avg = statistics.mean(scores)
            if avg >= _STRENGTH_THRESHOLD:
                std = statistics.stdev(scores) if len(scores) > 1 else 0.0
                consistency = 1.0 - (std / avg) if avg > 0 else 0.0
                consistency = max(0.0, min(1.0, consistency))

                strengths.append(
                    StrengthResponse(
                        criterion_name=criterion_name,
                        avg_score=round(avg, 2),
                        consistency=round(consistency, 2),
                    )
                )

        return sorted(strengths, key=lambda s: s.avg_score, reverse=True)

    @staticmethod
    def _gap_suggestion(criterion: str) -> Optional[str]:
        suggestions = {
            "Precisão": "Revise conceitos fundamentais e pratique com exemplos",
            "Clareza": "Trabalhe a estrutura e organização do texto",
            "Argumentação": "Estude raciocínio lógico e apresentação de evidências",
            "Profundidade": "Explore materiais avançados e casos limites",
        }
        return suggestions.get(
            criterion,
            f"Dedique prática direcionada ao critério '{criterion}'",
        )

    # =======================================================================
    # Agregação de turma
    # =======================================================================

    def _aggregate_class_analytics(
        self,
        class_uuid: UUID,
        class_name: str,
        profiles: List[StudentPerformanceResponse],
    ) -> ClassAnalyticsResponse:
        """Agrega os perfis individuais em insights de turma."""
        all_scores = [p.avg_score for p in profiles if p.submission_count > 0]

        if not all_scores:
            return self._empty_class_analytics(class_uuid, class_name)

        class_avg = statistics.mean(all_scores)
        class_median = statistics.median(all_scores)
        class_std = statistics.stdev(all_scores) if len(all_scores) > 1 else 0.0

        struggling: List[ClassStudentSummaryResponse] = []
        top_performers: List[ClassStudentSummaryResponse] = []
        all_students: List[ClassStudentSummaryResponse] = []

        for p in profiles:
            summary = ClassStudentSummaryResponse(
                student_uuid=p.student_uuid,
                student_name=p.student_name,
                avg_score=p.avg_score,
                submission_count=p.submission_count,
                trend=p.trend,
            )
            all_students.append(summary)

            if p.submission_count >= _TREND_MIN_SAMPLES:
                if p.avg_score < (class_avg - class_std):
                    struggling.append(summary)
                elif p.avg_score > (class_avg + class_std):
                    top_performers.append(summary)

        grade_distribution = self._calculate_grade_distribution(all_scores)
        most_common_gaps = self._aggregate_class_gaps(profiles)
        total_submissions = sum(p.submission_count for p in profiles)

        return ClassAnalyticsResponse(
            class_uuid=class_uuid,
            class_name=class_name,
            total_students=len(profiles),
            total_submissions=total_submissions,
            class_avg_score=round(class_avg, 2),
            median_score=round(class_median, 2),
            std_deviation=round(class_std, 2),
            grade_distribution=grade_distribution,
            struggling_students=struggling,
            top_performers=top_performers,
            most_common_gaps=most_common_gaps,
            students=all_students,
        )

    @staticmethod
    def _calculate_grade_distribution(scores: List[float]) -> List[GradeDistributionResponse]:
        """Distribui notas nos buckets A/B/C/D/F."""
        buckets = [
            ("A", "9-10", lambda s: s >= 9.0),
            ("B", "7-9", lambda s: 7.0 <= s < 9.0),
            ("C", "5-7", lambda s: 5.0 <= s < 7.0),
            ("D", "3-5", lambda s: 3.0 <= s < 5.0),
            ("F", "0-3", lambda s: s < 3.0),
        ]
        total = len(scores) or 1
        return [
            GradeDistributionResponse(
                label=label,
                range=rng,
                count=sum(1 for s in scores if predicate(s)),
                percentage=round(sum(1 for s in scores if predicate(s)) / total * 100, 1),
            )
            for label, rng, predicate in buckets
        ]

    @staticmethod
    def _aggregate_class_gaps(
        profiles: List[StudentPerformanceResponse],
    ) -> List[LearningGapResponse]:
        """Agrega gaps individuais para encontrar os mais comuns na turma."""
        gap_counts: Dict[str, List[float]] = defaultdict(list)

        for profile in profiles:
            for gap in profile.learning_gaps:
                gap_counts[gap.criterion_name].append(gap.avg_score)

        aggregated: List[LearningGapResponse] = []
        for criterion_name, avg_scores in gap_counts.items():
            class_avg = statistics.mean(avg_scores)
            if class_avg < 4.0:
                severity = "high"
            elif class_avg < 5.5:
                severity = "medium"
            else:
                severity = "low"

            aggregated.append(
                LearningGapResponse(
                    criterion_name=criterion_name,
                    severity=severity,
                    evidence_count=len(avg_scores),
                    avg_score=round(class_avg, 2),
                )
            )

        return sorted(aggregated, key=lambda g: g.avg_score)[:5]

    @staticmethod
    def _empty_class_analytics(class_uuid: UUID, class_name: str) -> ClassAnalyticsResponse:
        return ClassAnalyticsResponse(
            class_uuid=class_uuid,
            class_name=class_name,
            total_students=0,
            total_submissions=0,
            class_avg_score=0.0,
            median_score=0.0,
            std_deviation=0.0,
        )
