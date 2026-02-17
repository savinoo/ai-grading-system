"""
Composer para controller de estatísticas do dashboard.
"""

from src.controllers.dashboard.get_dashboard_stats_controller import GetDashboardStatsController
from src.services.dashboard.dashboard_service import DashboardService

from src.models.repositories.exams_repository import ExamsRepository
from src.models.repositories.student_answer_repository import StudentAnswerRepository
from src.models.repositories.exam_question_repository import ExamQuestionRepository
from src.models.repositories.classes_repository import ClassesRepository
from src.models.repositories.class_student_repository import ClassStudentRepository


def make_get_dashboard_stats_controller() -> GetDashboardStatsController:
    """
    Factory para criar GetDashboardStatsController com suas dependências.
    """
    exam_repository = ExamsRepository()
    student_answer_repository = StudentAnswerRepository()
    exam_question_repository = ExamQuestionRepository()
    class_repository = ClassesRepository()
    class_student_repository = ClassStudentRepository()
    
    service = DashboardService(
        exam_repository=exam_repository,
        student_answer_repository=student_answer_repository,
        exam_question_repository=exam_question_repository,
        class_repository=class_repository,
        class_student_repository=class_student_repository
    )
    
    return GetDashboardStatsController(dashboard_service=service)

