"""Analytics module for Professor Assistant features"""
from src.analytics.class_insights import ClassAnalyzer
from src.analytics.plagiarism_detector import PlagiarismDetector, PlagiarismReport
from src.analytics.student_tracker import StudentTracker

__all__ = ["StudentTracker", "ClassAnalyzer", "PlagiarismDetector", "PlagiarismReport"]
