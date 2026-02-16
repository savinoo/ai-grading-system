"""
Serviço para buscar resultados e estatísticas de correção.
"""

import statistics
from datetime import datetime
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from src.interfaces.services.results.results_service_interface import ResultsServiceInterface
from src.domain.responses.results import (
    ExamResultsResponse,
    ExamStatistics,
    QuestionStatistics,
    ScoreDistribution,
    GradingDetailsResponse,
    StudentInfo,
    QuestionInfo,
    CriterionScoreDetail,
    AgentScoreBreakdown,
    ExamResultsSummaryResponse
)

from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.student_answer_repository_interface import StudentAnswerRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.student_repository_interface import StudentRepositoryInterface
from src.interfaces.repositories.grading_criteria_repository_interface import GradingCriteriaRepositoryInterface
from src.interfaces.repositories.exam_criteria_repository_interface import ExamCriteriaRepositoryInterface

from src.models.entities.student_answer_criteria_scores import StudentAnswerCriteriaScore
from src.models.entities.student_answers import StudentAnswer

from src.errors.domain.not_found import NotFoundError
from src.core.logging_config import get_logger


logger = get_logger(__name__)


class ResultsService(ResultsServiceInterface):
    """Implementação do serviço de resultados."""
    
    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        student_answer_repository: StudentAnswerRepositoryInterface,
        exam_question_repository: ExamQuestionRepositoryInterface,
        student_repository: StudentRepositoryInterface,
        grading_criteria_repository: GradingCriteriaRepositoryInterface,
        exam_criteria_repository: ExamCriteriaRepositoryInterface
    ):
        self.__exam_repository = exam_repository
        self.__student_answer_repository = student_answer_repository
        self.__exam_question_repository = exam_question_repository
        self.__student_repository = student_repository
        self.__grading_criteria_repository = grading_criteria_repository
        self.__exam_criteria_repository = exam_criteria_repository
    
    def get_exam_results(self, db: Session, exam_uuid: UUID) -> ExamResultsResponse:
        """Retorna estatísticas de uma prova corrigida."""
        
        # Buscar prova
        exam = self.__exam_repository.get_by_uuid(db, exam_uuid)
        if not exam:
            raise NotFoundError(f"Prova {exam_uuid} não encontrada")
        
        # Buscar todas as respostas da prova
        answers = db.query(StudentAnswer).filter(
            StudentAnswer.exam_uuid == exam_uuid,
            StudentAnswer.is_graded.is_(True)
        ).all()
        
        if not answers:
            # Prova sem respostas corrigidas
            return ExamResultsResponse(
                exam_uuid=exam_uuid,
                exam_title=exam.title,
                status="PENDING",
                graded_at=None,
                statistics=ExamStatistics(
                    total_students=0,
                    total_questions=0,
                    arbiter_rate=0.0,
                    average_score=0.0,
                    std_deviation=0.0,
                    max_score=0.0,
                    min_score=0.0,
                    median=0.0,
                    distribution=[]
                ),
                questions_stats=[]
            )
        
        # Calcular estatísticas gerais
        scores = [answer.score for answer in answers if answer.score is not None]
        
        # Contar respostas que precisaram de árbitro
        # NOTA: Requer tabela de logs de arbitração para implementação completa
        # Por ora, consideramos 0 até que a estrutura seja criada
        arbiter_count = 0
        total_answers = len(answers)
        
        # Distribuição de notas
        distribution = self.__calculate_distribution(scores)
        
        # Estatísticas por questão
        questions_stats = self.__calculate_questions_stats(db, exam_uuid)
        
        exam_stats = ExamStatistics(
            total_students=len(set(a.student_uuid for a in answers)),
            total_questions=len(questions_stats),
            arbiter_rate=(arbiter_count / total_answers * 100) if total_answers > 0 else 0.0,
            average_score=statistics.mean(scores) if scores else 0.0,
            std_deviation=statistics.stdev(scores) if len(scores) > 1 else 0.0,
            max_score=max(scores) if scores else 0.0,
            min_score=min(scores) if scores else 0.0,
            median=statistics.median(scores) if scores else 0.0,
            distribution=distribution
        )
        
        return ExamResultsResponse(
            exam_uuid=exam_uuid,
            exam_title=exam.title,
            status="GRADED" if len(answers) > 0 else "PENDING",
            graded_at=max((a.graded_at for a in answers if a.graded_at), default=None),
            statistics=exam_stats,
            questions_stats=questions_stats
        )
    
    def list_exams_results(self, db: Session, user_uuid: str) -> List[ExamResultsSummaryResponse]:
        """Retorna lista de provas com resultados do professor."""
        
        # Buscar provas do professor
        exams = self.__exam_repository.get_by_teacher(db, UUID(user_uuid))
        
        if not exams:
            return []
        
        results_list = []
        
        for exam in exams:
            # Buscar respostas corrigidas da prova
            answers = db.query(StudentAnswer).filter(
                StudentAnswer.exam_uuid == exam.uuid,
                StudentAnswer.is_graded.is_(True)
            ).all()
            
            if not answers:
                # Prova sem respostas corrigidas ainda
                continue
            
            # Calcular estatísticas resumidas
            scores = [answer.score for answer in answers if answer.score is not None]
            total_students = len(set(a.student_uuid for a in answers))
            
            # Contar árbitros (por ora 0 até implementar tabela de logs)
            arbiter_count = 0
            total_answers = len(answers)
            
            # Determinar status
            # Se todas as questões de todos os alunos foram corrigidas: GRADED
            # Se algumas foram corrigidas: PARTIAL
            # Se nenhuma foi corrigida: PENDING
            questions = self.__exam_question_repository.get_by_exam(db, exam.uuid)
            total_expected_answers = total_students * len(questions)
            
            if len(answers) == total_expected_answers:
                status = "GRADED"
            elif len(answers) > 0:
                status = "PARTIAL"
            else:
                status = "PENDING"
            
            results_list.append(
                ExamResultsSummaryResponse(
                    exam_uuid=exam.uuid,
                    exam_title=exam.title,
                    status=status,
                    graded_at=max((a.graded_at for a in answers if a.graded_at), default=None),
                    total_students=total_students,
                    average_score=statistics.mean(scores) if scores else 0.0,
                    arbiter_rate=(arbiter_count / total_answers * 100) if total_answers > 0 else 0.0
                )
            )
        
        # Ordenar por data de correção (mais recentes primeiro)
        results_list.sort(key=lambda x: x.graded_at or datetime.min, reverse=True)
        
        return results_list
    
    def get_grading_details(
        self,
        db: Session,
        answer_uuid: UUID
    ) -> GradingDetailsResponse:
        """Retorna detalhes completos da correção de uma resposta."""
        
        # Buscar resposta
        answer = self.__student_answer_repository.get_by_uuid(db, answer_uuid)
        if not answer:
            raise NotFoundError(f"Resposta {answer_uuid} não encontrada")
        
        # Buscar questão
        question = self.__exam_question_repository.get_by_uuid(db, answer.question_uuid)
        if not question:
            raise NotFoundError(f"Questão {answer.question_uuid} não encontrada")
        
        # Buscar aluno
        student = self.__student_repository.get_by_uuid(db, answer.student_uuid)
        if not student:
            raise NotFoundError(f"Aluno {answer.student_uuid} não encontrada")
        
        # Buscar scores por critério
        criteria_scores_entities = db.query(StudentAnswerCriteriaScore).filter(
            StudentAnswerCriteriaScore.student_answer_uuid == answer_uuid
        ).all()
        
        # Montar scores por critério
        criteria_scores = []
        for score_entity in criteria_scores_entities:
            # Buscar nome do critério
            try:
                criteria = self.__grading_criteria_repository.get_by_uuid(db, score_entity.criteria_uuid)
                criterion_name = criteria.name
            except Exception:
                criterion_name = "Critério"
                logger.warning("Não foi possível buscar nome do critério: %s", score_entity.criteria_uuid)
            
            # Buscar max_score do critério da questão/prova
            try:
                # Buscar critérios da prova para pegar max_points
                exam_criteria_list = self.__exam_criteria_repository.get_by_exam(db, answer.exam_uuid)
                criterion_config = next(
                    (ec for ec in exam_criteria_list if ec.criteria_uuid == score_entity.criteria_uuid),
                    None
                )
                max_score = float(criterion_config.max_points) if criterion_config and criterion_config.max_points else 10.0
            except Exception:
                max_score = 10.0
                logger.warning("Não foi possível buscar max_score do critério: %s", score_entity.criteria_uuid)
            
            # NOTA: AgentScoreBreakdown requer tabela de correções individuais dos agentes
            # Por ora, retornamos vazio até que a estrutura seja criada
            criteria_scores.append(
                CriterionScoreDetail(
                    criterion_uuid=score_entity.criteria_uuid,
                    criterion_name=criterion_name,
                    max_score=max_score,
                    raw_score=score_entity.raw_score,
                    weighted_score=score_entity.weighted_score,
                    feedback=score_entity.feedback,
                    agent_scores=AgentScoreBreakdown()
                )
            )
        
        # NOTA: Buscar correções dos agentes requer tabela de logs (ex: agent_correction_logs)
        # Esta funcionalidade será implementada quando a persistência dos agentes for adicionada
        corrections = []
        
        # NOTA: Buscar contexto RAG usado requer tabela de logs de RAG
        # Esta funcionalidade será implementada quando a persistência do RAG for adicionada
        rag_context = []
        
        # Calcular max_score da questão baseado nos critérios
        try:
            exam_criteria_list = self.__exam_criteria_repository.get_by_exam(db, answer.exam_uuid)
            total_max_score = sum(
                float(ec.max_points) if ec.max_points else 0.0
                for ec in exam_criteria_list
            )
            question_max_score = total_max_score if total_max_score > 0 else 10.0
        except Exception:
            question_max_score = 10.0
            logger.warning("Não foi possível calcular max_score da questão: %s", question.uuid)
        
        return GradingDetailsResponse(
            answer_uuid=answer_uuid,
            student=StudentInfo(
                uuid=student.uuid,
                name=student.name,
                email=student.email
            ),
            question=QuestionInfo(
                uuid=question.uuid,
                statement=question.statement,
                max_score=question_max_score
            ),
            answer_text=answer.answer or "",
            final_score=answer.score or 0.0,
            status=answer.status,
            graded_at=answer.graded_at,
            final_feedback=answer.feedback or "",
            # Detectar divergência (requer múltiplas correções salvas)
            # NOTA: Implementação completa requer persistência de correções individuais
            divergence_detected=False,
            divergence_value=None,
            criteria_scores=criteria_scores,
            corrections=corrections,
            rag_context=rag_context
        )
    
    def __calculate_distribution(self, scores: List[float]) -> List[ScoreDistribution]:
        """Calcula distribuição de notas por faixa."""
        
        ranges = [
            ("0-2", 0, 2),
            ("2-4", 2, 4),
            ("4-6", 4, 6),
            ("6-8", 6, 8),
            ("8-10", 8, 10)
        ]
        
        distribution = []
        for range_name, min_val, max_val in ranges:
            count = sum(1 for score in scores if min_val <= score < max_val or (max_val == 10 and score == 10))
            distribution.append(ScoreDistribution(range=range_name, count=count))
        
        return distribution
    
    def __calculate_questions_stats(
        self,
        db: Session,
        exam_uuid: UUID
    ) -> List[QuestionStatistics]:
        """Calcula estatísticas por questão."""
        
        # Buscar questões da prova
        questions = self.__exam_question_repository.get_by_exam(db, exam_uuid)
        
        stats = []
        for idx, question in enumerate(questions, start=1):
            # Buscar respostas desta questão
            answers = db.query(StudentAnswer).filter(
                StudentAnswer.question_uuid == question.uuid,
                StudentAnswer.is_graded.is_(True)
            ).all()
            
            scores = [a.score for a in answers if a.score is not None]
            
            if scores:
                # Calcular max_score da questão baseado nos critérios
                try:
                    exam_criteria_list = self.__exam_criteria_repository.get_by_exam(db, exam_uuid)
                    total_max_score = sum(
                        float(ec.max_points) if ec.max_points else 0.0
                        for ec in exam_criteria_list
                    )
                    question_max_score = total_max_score if total_max_score > 0 else 10.0
                except Exception:
                    question_max_score = 10.0
                    logger.warning("Não foi possível calcular max_score da questão %s", question.uuid)
                
                # NOTA: arbiter_count requer tabela de logs de arbitração
                arbiter_count_question = 0
                
                stats.append(
                    QuestionStatistics(
                        question_uuid=question.uuid,
                        question_number=idx,
                        question_title=question.statement[:50] + "..." if len(question.statement) > 50 else question.statement,
                        average_score=statistics.mean(scores),
                        std_deviation=statistics.stdev(scores) if len(scores) > 1 else 0.0,
                        max_score=question_max_score,
                        min_score=min(scores),
                        arbiter_count=arbiter_count_question
                    )
                )
        
        return stats
