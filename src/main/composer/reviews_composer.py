from src.controllers.reviews.get_exam_review_controller import GetExamReviewController
from src.controllers.reviews.adjust_grade_controller import AdjustGradeController
from src.controllers.reviews.finalize_review_controller import FinalizeReviewController
from src.controllers.reviews.approve_answer_controller import ApproveAnswerController
from src.controllers.reviews.download_exam_report_controller import DownloadExamReportController

from src.services.reviews.exam_review_query_service import ExamReviewQueryService
from src.services.reviews.grade_adjustment_service import GradeAdjustmentService
from src.services.reviews.review_finalization_service import ReviewFinalizationService
from src.services.reviews.answer_approval_service import AnswerApprovalService

from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.student_answer_repository import StudentAnswerRepository
from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.student_repository import StudentRepository
from src.models.repositories.grading_criteria_repository import GradingCriteriaRepository
from src.models.repositories.exam_criteria_repository import ExamCriteriaRepository
from src.models.repositories.classes_repository import ClassesRepository


def make_get_exam_review_controller() -> GetExamReviewController:
    """Factory para GetExamReviewController."""
    
    # Dependências para Query Service
    exam_repository = ExamsRepository()
    exam_question_repository = ExamQuestionRepository()
    student_repository = StudentRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    class_repository = ClassesRepository()
    
    query_service = ExamReviewQueryService(
        exam_repository=exam_repository,
        exam_question_repository=exam_question_repository,
        student_repository=student_repository,
        grading_criteria_repository=grading_criteria_repository,
        exam_criteria_repository=exam_criteria_repository,
        class_repository=class_repository
    )
    
    return GetExamReviewController(query_service=query_service)


def make_adjust_grade_controller() -> AdjustGradeController:
    """Factory para AdjustGradeController."""
    
    # Dependências para Adjustment Service
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    
    adjustment_service = GradeAdjustmentService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository
    )
    
    return AdjustGradeController(adjustment_service=adjustment_service)


def make_finalize_review_controller() -> FinalizeReviewController:
    """Factory para FinalizeReviewController."""
    
    # Dependências para Finalization Service
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    
    finalization_service = ReviewFinalizationService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository
    )
    
    return FinalizeReviewController(finalization_service=finalization_service)


def make_approve_answer_controller() -> ApproveAnswerController:
    """Factory para ApproveAnswerController."""
    
    # Dependências para Approval Service
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    
    approval_service = AnswerApprovalService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository
    )
    
    return ApproveAnswerController(approval_service=approval_service)


def make_download_exam_report_controller() -> DownloadExamReportController:
    """Factory para DownloadExamReportController."""
    return DownloadExamReportController()
