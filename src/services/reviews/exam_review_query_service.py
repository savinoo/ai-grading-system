from uuid import UUID
from sqlalchemy.orm import Session

from src.domain.responses.reviews import (
    ExamReviewResponse,
    QuestionReview,
    StudentAnswerReview,
    CriterionScore
)

from src.interfaces.repositories.exams_repository_interfaces import ExamsRepositoryInterface
from src.interfaces.repositories.exam_question_repository_interface import ExamQuestionRepositoryInterface
from src.interfaces.repositories.student_repository_interface import StudentRepositoryInterface
from src.interfaces.repositories.grading_criteria_repository_interface import GradingCriteriaRepositoryInterface
from src.interfaces.repositories.exam_criteria_repository_interface import ExamCriteriaRepositoryInterface
from src.interfaces.repositories.classes_repository_interface import ClassesRepositoryInterface

from src.interfaces.services.reviews.exam_review_query_service_interface import ExamReviewQueryServiceInterface

from src.models.entities.student_answer_criteria_scores import StudentAnswerCriteriaScore
from src.models.entities.student_answers import StudentAnswer

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError

from src.core.logging_config import get_logger


class ExamReviewQueryService(ExamReviewQueryServiceInterface):
    """Serviço para consulta de dados de revisão de provas."""
    
    def __init__(
        self,
        exam_repository: ExamsRepositoryInterface,
        exam_question_repository: ExamQuestionRepositoryInterface,
        student_repository: StudentRepositoryInterface,
        grading_criteria_repository: GradingCriteriaRepositoryInterface,
        exam_criteria_repository: ExamCriteriaRepositoryInterface,
        class_repository: ClassesRepositoryInterface
    ):
        self.__exam_repository = exam_repository
        self.__exam_question_repository = exam_question_repository
        self.__student_repository = student_repository
        self.__grading_criteria_repository = grading_criteria_repository
        self.__exam_criteria_repository = exam_criteria_repository
        self.__class_repository = class_repository
        self.__logger = get_logger(__name__)
    
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
                self.__logger.warning("Não foi possível buscar nome da turma: %s", exam.class_uuid)
        
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
                self.__logger.warning("Erro ao buscar critério %s: %s", ec.criteria_uuid, str(e))
        
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
                    self.__logger.warning("Não foi possível buscar aluno: %s", answer.student_uuid)
                
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
                        self.__logger.warning("Não foi possível buscar critério: %s", score_entity.criteria_uuid)
                    
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
                        graded_at=answer.graded_at
                    )
                )
            
            # Usar pontuação da questão
            question_max_score = float(question.points) if question.points else 10.0
            
            questions_review.append(
                QuestionReview(
                    question_uuid=question.uuid,
                    question_number=idx,
                    statement=question.statement,
                    expected_answer=None,
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
