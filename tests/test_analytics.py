"""
Unit tests for analytics modules
"""
import pytest
from datetime import datetime, timedelta

from src.domain.analytics_schemas import (
    SubmissionRecord, StudentProfile, LearningGap, ClassInsights
)
from src.analytics import StudentTracker, ClassAnalyzer


class TestStudentTracker:
    """Tests for StudentTracker"""
    
    def test_add_single_submission(self):
        """Test adding first submission to new student"""
        tracker = StudentTracker()
        
        submission = SubmissionRecord(
            submission_id="SUB001",
            question_id="Q1",
            question_text="Test question",
            student_answer="Test answer",
            grade=8.5,
            max_score=10.0,
            criterion_scores={"Precisão": 8.0, "Clareza": 9.0}
        )
        
        profile = tracker.add_submission(
            student_id="S001",
            student_name="Test Student",
            submission=submission
        )
        
        assert profile.student_id == "S001"
        assert profile.student_name == "Test Student"
        assert len(profile.submissions_history) == 1
        assert profile.avg_grade == 8.5
        assert profile.trend == "insufficient_data"  # Only 1 submission
    
    def test_trend_detection_improving(self):
        """Test that improving grades are detected"""
        tracker = StudentTracker()
        
        # Simulate improving student (5 → 9)
        grades = [5.0, 6.0, 7.0, 8.0, 9.0]
        for i, grade in enumerate(grades):
            submission = SubmissionRecord(
                submission_id=f"SUB{i}",
                question_id=f"Q{i}",
                question_text=f"Question {i}",
                student_answer="Answer",
                grade=grade,
                max_score=10.0,
                timestamp=datetime.now() + timedelta(days=i)
            )
            tracker.add_submission("S002", "Improving Student", submission)
        
        profile = tracker.get_profile("S002")
        assert profile.trend == "improving"
        assert profile.trend_confidence > 0.8  # Strong linear fit
    
    def test_trend_detection_declining(self):
        """Test that declining performance is detected"""
        tracker = StudentTracker()
        
        # Simulate declining student (9 → 5)
        grades = [9.0, 8.0, 7.0, 6.0, 5.0]
        for i, grade in enumerate(grades):
            submission = SubmissionRecord(
                submission_id=f"SUB{i}",
                question_id=f"Q{i}",
                question_text=f"Question {i}",
                student_answer="Answer",
                grade=grade,
                max_score=10.0,
                timestamp=datetime.now() + timedelta(days=i)
            )
            tracker.add_submission("S003", "Declining Student", submission)
        
        profile = tracker.get_profile("S003")
        assert profile.trend == "declining"
    
    def test_learning_gap_identification(self):
        """Test that consistent low scores create learning gaps"""
        tracker = StudentTracker()
        
        # Consistently low on "Precisão", high on "Clareza"
        for i in range(5):
            submission = SubmissionRecord(
                submission_id=f"SUB{i}",
                question_id=f"Q{i}",
                question_text=f"Question {i}",
                student_answer="Answer",
                grade=6.5,
                max_score=10.0,
                criterion_scores={"Precisão": 4.0, "Clareza": 9.0}
            )
            tracker.add_submission("S004", "Gap Student", submission)
        
        profile = tracker.get_profile("S004")
        
        # Should have identified "Precisão" as a gap
        gap_names = [g.criterion_name for g in profile.learning_gaps]
        assert "Precisão" in gap_names
        
        # Should NOT have "Clareza" as a gap (it's a strength)
        assert "Clareza" not in gap_names
        
        # Should have identified "Clareza" as a strength
        strength_names = [s.criterion_name for s in profile.strengths]
        assert "Clareza" in strength_names


class TestClassAnalyzer:
    """Tests for ClassAnalyzer"""
    
    def test_empty_class(self):
        """Test that empty class returns zero metrics"""
        analyzer = ClassAnalyzer()
        insights = analyzer.analyze_class("CLASS001", [])
        
        assert insights.total_students == 0
        assert insights.class_avg_grade == 0.0
    
    def test_grade_distribution(self):
        """Test letter grade bucketing"""
        analyzer = ClassAnalyzer()
        
        # Create mock profiles with known grades
        profiles = []
        grades = [9.5, 8.0, 6.5, 4.0, 2.0]  # A, B, C, D, F
        
        for i, grade in enumerate(grades):
            profile = StudentProfile(
                student_id=f"S{i}",
                student_name=f"Student {i}",
                avg_grade=grade
            )
            submission = SubmissionRecord(
                submission_id=f"SUB{i}",
                question_id="Q1",
                question_text="Test",
                student_answer="Test",
                grade=grade,
                max_score=10.0
            )
            profile.submissions_history.append(submission)
            profiles.append(profile)
        
        insights = analyzer.analyze_class("CLASS001", profiles)
        
        # Check distribution
        dist = insights.grade_distribution
        assert dist["A"] == 1
        assert dist["B"] == 1
        assert dist["C"] == 1
        assert dist["D"] == 1
        assert dist["F"] == 1
    
    def test_outlier_detection(self):
        """Test that statistical outliers are identified"""
        analyzer = ClassAnalyzer()
        
        # Class average ~7.0, with one very high and one very low
        grades = [7.0, 7.5, 6.5, 7.0, 9.5, 3.0, 7.0]
        profiles = []
        
        for i, grade in enumerate(grades):
            profile = StudentProfile(
                student_id=f"S{i}",
                student_name=f"Student {i}",
                avg_grade=grade,
                submission_count=3  # Minimum for outlier detection
            )
            # Add mock submissions
            for _ in range(3):
                profile.submissions_history.append(
                    SubmissionRecord(
                        submission_id=f"SUB{i}",
                        question_id="Q1",
                        question_text="Test",
                        student_answer="Test",
                        grade=grade,
                        max_score=10.0
                    )
                )
            profiles.append(profile)
        
        insights = analyzer.analyze_class("CLASS001", profiles)
        
        # Should identify outliers
        assert len(insights.struggling_students) >= 1
        assert len(insights.top_performers) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
