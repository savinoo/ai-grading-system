"""
Serviços de análise pedagógica.
"""

from .analytics_service import AnalyticsService
from .plagiarism_service import PlagiarismService
from .student_knowledge_service import StudentKnowledgeService

__all__ = ["AnalyticsService", "PlagiarismService", "StudentKnowledgeService"]
