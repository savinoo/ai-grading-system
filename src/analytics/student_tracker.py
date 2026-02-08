"""
Student Performance Tracker
Analyzes individual student evolution and identifies learning patterns.
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional
from statistics import mean, stdev
import numpy as np

from src.domain.analytics_schemas import (
    StudentProfile, SubmissionRecord, LearningGap, Strength
)

logger = logging.getLogger(__name__)


class StudentTracker:
    """
    Tracks student performance over time and generates insights.
    """
    
    def __init__(self):
        self.profiles: Dict[str, StudentProfile] = {}
    
    def add_submission(
        self,
        student_id: str,
        student_name: str,
        submission: SubmissionRecord
    ) -> StudentProfile:
        """
        Add a new submission and update student profile.
        """
        if student_id not in self.profiles:
            self.profiles[student_id] = StudentProfile(
                student_id=student_id,
                student_name=student_name
            )
        
        profile = self.profiles[student_id]
        profile.submissions_history.append(submission)
        profile.submission_count = len(profile.submissions_history)
        profile.last_submission = submission.timestamp
        
        if profile.first_submission is None:
            profile.first_submission = submission.timestamp
        
        # Recompute metrics
        self._update_profile_metrics(profile)
        
        return profile
    
    def _update_profile_metrics(self, profile: StudentProfile):
        """Recalculate all derived metrics for a student"""
        if not profile.submissions_history:
            return
        
        # Basic stats
        grades = [s.grade for s in profile.submissions_history]
        profile.avg_grade = mean(grades)
        
        # Trend detection (linear regression on grades over time)
        if len(grades) >= 3:
            profile.trend, profile.trend_confidence = self._detect_trend(grades)
        
        # Identify learning gaps
        profile.learning_gaps = self._identify_gaps(profile)
        
        # Identify strengths
        profile.strengths = self._identify_strengths(profile)
        
        profile.last_updated = datetime.now()
    
    def _detect_trend(self, grades: List[float]) -> tuple[str, float]:
        """
        Use linear regression to detect if student is improving/declining.
        Returns: (trend_label, confidence)
        """
        if len(grades) < 3:
            return "insufficient_data", 0.0
        
        # Simple linear fit
        x = np.arange(len(grades))
        y = np.array(grades)
        
        # Calculate slope
        slope, _ = np.polyfit(x, y, 1)
        
        # Calculate R² for confidence
        y_pred = np.poly1d(np.polyfit(x, y, 1))(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Classify trend
        if abs(slope) < 0.1:  # Essentially flat
            return "stable", r_squared
        elif slope > 0:
            return "improving", r_squared
        else:
            return "declining", r_squared
    
    def _identify_gaps(self, profile: StudentProfile) -> List[LearningGap]:
        """
        Identify consistent low-performing criteria.
        A gap is a criterion where avg score < 60% of max.
        """
        gaps = []
        criterion_tracker: Dict[str, List[float]] = {}
        
        for sub in profile.submissions_history:
            for crit_name, score in sub.criterion_scores.items():
                if crit_name not in criterion_tracker:
                    criterion_tracker[crit_name] = []
                criterion_tracker[crit_name].append(score)
        
        for crit_name, scores in criterion_tracker.items():
            avg_score = mean(scores)
            
            # Threshold for gap: avg < 6.0 (assuming 10-point scale)
            if avg_score < 6.0:
                severity = "high" if avg_score < 4.0 else "medium" if avg_score < 5.5 else "low"
                
                gap = LearningGap(
                    criterion_name=crit_name,
                    topic="General",  # Could be inferred from question metadata
                    severity=severity,
                    evidence_count=len(scores),
                    avg_score=avg_score,
                    suggestion=self._generate_gap_suggestion(crit_name, avg_score)
                )
                gaps.append(gap)
        
        return sorted(gaps, key=lambda g: g.avg_score)
    
    def _identify_strengths(self, profile: StudentProfile) -> List[Strength]:
        """
        Identify criteria where student consistently performs well.
        """
        strengths = []
        criterion_tracker: Dict[str, List[float]] = {}
        
        for sub in profile.submissions_history:
            for crit_name, score in sub.criterion_scores.items():
                if crit_name not in criterion_tracker:
                    criterion_tracker[crit_name] = []
                criterion_tracker[crit_name].append(score)
        
        for crit_name, scores in criterion_tracker.items():
            avg_score = mean(scores)
            
            # Threshold for strength: avg > 8.0
            if avg_score >= 8.0:
                # Consistency = 1 - coefficient of variation
                std = stdev(scores) if len(scores) > 1 else 0
                consistency = 1 - (std / avg_score) if avg_score > 0 else 0
                consistency = max(0, min(1, consistency))  # Clamp to [0,1]
                
                strength = Strength(
                    criterion_name=crit_name,
                    topic="General",
                    avg_score=avg_score,
                    consistency=consistency
                )
                strengths.append(strength)
        
        return sorted(strengths, key=lambda s: s.avg_score, reverse=True)
    
    def _generate_gap_suggestion(self, criterion: str, avg_score: float) -> str:
        """Generate actionable suggestion for improving this criterion"""
        suggestions = {
            "Precisão": "Review fundamental concepts and examples",
            "Clareza": "Practice structured writing and organization",
            "Argumentação": "Study logical reasoning and evidence presentation",
            "Profundidade": "Read advanced materials and explore edge cases"
        }
        
        return suggestions.get(
            criterion,
            f"Focus on improving {criterion} through targeted practice"
        )
    
    def get_profile(self, student_id: str) -> Optional[StudentProfile]:
        """Retrieve student profile"""
        return self.profiles.get(student_id)
    
    def get_all_profiles(self) -> List[StudentProfile]:
        """Get all tracked student profiles"""
        return list(self.profiles.values())
    
    def export_profile(self, student_id: str) -> Optional[dict]:
        """Export profile as JSON-serializable dict"""
        profile = self.get_profile(student_id)
        return profile.model_dump() if profile else None
