"""
Composers para controllers de análise pedagógica.
"""

from src.controllers.analytics.list_classes_analytics_controller import ListClassesAnalyticsController
from src.controllers.analytics.get_class_analytics_controller import GetClassAnalyticsController
from src.controllers.analytics.get_student_performance_controller import GetStudentPerformanceController

from src.services.analytics.analytics_service import AnalyticsService

from src.models.repositories.classes_repository import ClassesRepository
from src.models.repositories.student_repository import StudentRepository


def _make_analytics_service() -> AnalyticsService:
    return AnalyticsService(
        classes_repository=ClassesRepository(),
        student_repository=StudentRepository(),
    )


def make_list_classes_analytics_controller() -> ListClassesAnalyticsController:
    """Factory para ListClassesAnalyticsController."""
    return ListClassesAnalyticsController(service=_make_analytics_service())


def make_get_class_analytics_controller() -> GetClassAnalyticsController:
    """Factory para GetClassAnalyticsController."""
    return GetClassAnalyticsController(service=_make_analytics_service())


def make_get_student_performance_controller() -> GetStudentPerformanceController:
    """Factory para GetStudentPerformanceController."""
    return GetStudentPerformanceController(service=_make_analytics_service())
