"""
Composers para controllers de revisão.
"""

from src.controllers.reviews.get_exam_review_controller import GetExamReviewController
from src.controllers.reviews.accept_suggestion_controller import AcceptSuggestionController
from src.controllers.reviews.reject_suggestion_controller import RejectSuggestionController
from src.controllers.reviews.adjust_grade_controller import AdjustGradeController
from src.controllers.reviews.finalize_review_controller import FinalizeReviewController

from src.services.reviews.review_service import ReviewService

from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.student_answer_repository import StudentAnswerRepository
from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.student_repository import StudentRepository
from src.models.repositories.grading_criteria_repository import GradingCriteriaRepository
from src.models.repositories.exam_criteria_repository import ExamCriteriaRepository
from src.models.repositories.classes_repository import ClassesRepository


def make_get_exam_review_controller() -> GetExamReviewController:
    """Factory para GetExamReviewController."""
    
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    student_repository = StudentRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    class_repository = ClassesRepository()
    
    service = ReviewService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository,
        exam_question_repository=exam_question_repository,
        student_repository=student_repository,
        grading_criteria_repository=grading_criteria_repository,
        exam_criteria_repository=exam_criteria_repository,
        class_repository=class_repository
    )
    
    return GetExamReviewController(review_service=service)


def make_accept_suggestion_controller() -> AcceptSuggestionController:
    """Factory para AcceptSuggestionController."""
    
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    student_repository = StudentRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    class_repository = ClassesRepository()
    
    service = ReviewService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository,
        exam_question_repository=exam_question_repository,
        student_repository=student_repository,
        grading_criteria_repository=grading_criteria_repository,
        exam_criteria_repository=exam_criteria_repository,
        class_repository=class_repository
    )
    
    return AcceptSuggestionController(review_service=service)


def make_reject_suggestion_controller() -> RejectSuggestionController:
    """Factory para RejectSuggestionController."""
    
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    student_repository = StudentRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    class_repository = ClassesRepository()
    
    service = ReviewService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository,
        exam_question_repository=exam_question_repository,
        student_repository=student_repository,
        grading_criteria_repository=grading_criteria_repository,
        exam_criteria_repository=exam_criteria_repository,
        class_repository=class_repository
    )
    
    return RejectSuggestionController(review_service=service)


def make_adjust_grade_controller() -> AdjustGradeController:
    """Factory para AdjustGradeController."""
    
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    student_repository = StudentRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    class_repository = ClassesRepository()
    
    service = ReviewService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository,
        exam_question_repository=exam_question_repository,
        student_repository=student_repository,
        grading_criteria_repository=grading_criteria_repository,
        exam_criteria_repository=exam_criteria_repository,
        class_repository=class_repository
    )
    
    return AdjustGradeController(review_service=service)


def make_finalize_review_controller() -> FinalizeReviewController:
    """Factory para FinalizeReviewController."""
    
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    student_repository = StudentRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    class_repository = ClassesRepository()
    
    service = ReviewService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository,
        exam_question_repository=exam_question_repository,
        student_repository=student_repository,
        grading_criteria_repository=grading_criteria_repository,
        exam_criteria_repository=exam_criteria_repository,
        class_repository=class_repository
    )
    
    return FinalizeReviewController(review_service=service)
