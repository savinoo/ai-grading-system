"""
Composers para controllers de resultados.
"""

from src.controllers.results.get_exam_results_controller import GetExamResultsController
from src.controllers.results.get_grading_details_controller import GetGradingDetailsController
from src.controllers.results.list_exams_results_controller import ListExamsResultsController

from src.services.results.results_service import ResultsService

from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.student_answer_repository import StudentAnswerRepository
from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.student_repository import StudentRepository
from src.models.repositories.grading_criteria_repository import GradingCriteriaRepository
from src.models.repositories.exam_criteria_repository import ExamCriteriaRepository


def make_get_exam_results_controller() -> GetExamResultsController:
    """Factory para GetExamResultsController."""
    
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    student_repository = StudentRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    
    service = ResultsService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository,
        exam_question_repository=exam_question_repository,
        student_repository=student_repository,
        grading_criteria_repository=grading_criteria_repository,
        exam_criteria_repository=exam_criteria_repository
    )
    
    return GetExamResultsController(service=service)


def make_list_exams_results_controller() -> ListExamsResultsController:
    """Factory para ListExamsResultsController."""
    
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    student_repository = StudentRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    
    service = ResultsService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository,
        exam_question_repository=exam_question_repository,
        student_repository=student_repository,
        grading_criteria_repository=grading_criteria_repository,
        exam_criteria_repository=exam_criteria_repository
    )
    
    return ListExamsResultsController(service=service)


def make_get_grading_details_controller() -> GetGradingDetailsController:
    """Factory para GetGradingDetailsController."""
    
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    student_repository = StudentRepository()
    grading_criteria_repository = GradingCriteriaRepository()
    exam_criteria_repository = ExamCriteriaRepository()
    
    service = ResultsService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository,
        exam_question_repository=exam_question_repository,
        student_repository=student_repository,
        grading_criteria_repository=grading_criteria_repository,
        exam_criteria_repository=exam_criteria_repository
    )
    
    return GetGradingDetailsController(service=service)
