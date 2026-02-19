"""
Class-Level Analytics
Generates aggregate insights for entire classes.
"""
import logging
from typing import List, Dict
from statistics import mean, median, stdev

from src.domain.analytics_schemas import (
    ClassInsights, StudentProfile, LearningGap
)

logger = logging.getLogger(__name__)


class ClassAnalyzer:
    """
    Analyzes class-level patterns and generates teaching insights.
    """
    
    def analyze_class(
        self,
        class_id: str,
        student_profiles: List[StudentProfile],
        question_data: List[Dict] = None
    ) -> ClassInsights:
        """
        Generate comprehensive class insights from student profiles.
        
        Args:
            class_id: Identifier for this class
            student_profiles: List of all student profiles
            question_data: Optional list of question metadata for difficulty ranking
        """
        if not student_profiles:
            return ClassInsights(
                class_id=class_id,
                total_students=0,
                total_submissions=0,
                class_avg_grade=0.0,
                median_grade=0.0,
                std_deviation=0.0
            )
        
        # Collect all grades
        all_grades = []
        for profile in student_profiles:
            all_grades.extend([s.grade for s in profile.submissions_history])
        
        if not all_grades:
            return ClassInsights(
                class_id=class_id,
                total_students=len(student_profiles),
                total_submissions=0,
                class_avg_grade=0.0,
                median_grade=0.0,
                std_deviation=0.0
            )
        
        # Basic statistics
        class_avg = mean(all_grades)
        class_median = median(all_grades)
        class_std = stdev(all_grades) if len(all_grades) > 1 else 0.0
        
        # Grade distribution
        distribution = self._calculate_distribution(all_grades)
        
        # Outlier detection
        struggling = self._find_struggling_students(
            student_profiles, class_avg, class_std
        )
        top_performers = self._find_top_performers(
            student_profiles, class_avg, class_std
        )
        
        # Common gaps across class
        common_gaps = self._aggregate_learning_gaps(student_profiles)
        
        # Question difficulty ranking
        difficult_questions = []
        if question_data:
            difficult_questions = self._rank_question_difficulty(
                question_data, student_profiles
            )
        
        return ClassInsights(
            class_id=class_id,
            total_students=len(student_profiles),
            total_submissions=sum(len(p.submissions_history) for p in student_profiles),
            class_avg_grade=class_avg,
            median_grade=class_median,
            std_deviation=class_std,
            grade_distribution=distribution,
            most_difficult_questions=difficult_questions,
            most_common_gaps=common_gaps,
            struggling_students=struggling,
            top_performers=top_performers
        )
    
    def _calculate_distribution(self, grades: List[float]) -> Dict[str, int]:
        """Bucket grades into letter grades"""
        buckets = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        
        for grade in grades:
            if grade >= 9.0:
                buckets["A"] += 1
            elif grade >= 7.0:
                buckets["B"] += 1
            elif grade >= 5.0:
                buckets["C"] += 1
            elif grade >= 3.0:
                buckets["D"] += 1
            else:
                buckets["F"] += 1
        
        return buckets
    
    def _find_struggling_students(
        self,
        profiles: List[StudentProfile],
        class_avg: float,
        class_std: float
    ) -> List[str]:
        """Students scoring >1 std dev below mean"""
        threshold = class_avg - class_std
        struggling = []
        
        for profile in profiles:
            if profile.avg_grade < threshold and profile.submission_count >= 3:
                struggling.append(profile.student_name)
        
        return struggling
    
    def _find_top_performers(
        self,
        profiles: List[StudentProfile],
        class_avg: float,
        class_std: float
    ) -> List[str]:
        """Students scoring >1 std dev above mean"""
        threshold = class_avg + class_std
        top = []
        
        for profile in profiles:
            if profile.avg_grade > threshold and profile.submission_count >= 3:
                top.append(profile.student_name)
        
        return top
    
    def _aggregate_learning_gaps(
        self,
        profiles: List[StudentProfile]
    ) -> List[LearningGap]:
        """
        Find learning gaps that appear across multiple students.
        These indicate curriculum-level issues.
        """
        gap_tracker: Dict[str, List[float]] = {}
        gap_topics: Dict[str, str] = {}
        
        for profile in profiles:
            for gap in profile.learning_gaps:
                key = gap.criterion_name
                if key not in gap_tracker:
                    gap_tracker[key] = []
                    gap_topics[key] = gap.topic
                gap_tracker[key].append(gap.avg_score)
        
        # Aggregate
        common_gaps = []
        for criterion, scores in gap_tracker.items():
            # Only consider it "common" if >=30% of class struggles
            affected_count = len(scores)
            if affected_count >= max(3, len(profiles) * 0.3):
                avg_score = mean(scores)
                severity = "high" if avg_score < 4.0 else "medium" if avg_score < 5.5 else "low"
                
                common_gaps.append(LearningGap(
                    criterion_name=criterion,
                    topic=gap_topics[criterion],
                    severity=severity,
                    evidence_count=affected_count,
                    avg_score=avg_score,
                    suggestion=f"Consider reviewing {criterion} in class - {affected_count} students struggling"
                ))
        
        return sorted(common_gaps, key=lambda g: g.evidence_count, reverse=True)
    
    def _rank_question_difficulty(
        self,
        question_data: List[Dict],
        profiles: List[StudentProfile]
    ) -> List[Dict]:
        """
        Rank questions by difficulty (avg score).
        Lower avg = harder question.
        """
        question_scores: Dict[str, List[float]] = {}
        
        for profile in profiles:
            for submission in profile.submissions_history:
                q_id = submission.question_id
                if q_id not in question_scores:
                    question_scores[q_id] = []
                question_scores[q_id].append(submission.grade)
        
        # Calculate avg and rank
        rankings = []
        for q_id, scores in question_scores.items():
            avg_score = mean(scores)
            rankings.append({
                "question_id": q_id,
                "avg_score": avg_score,
                "attempt_count": len(scores),
                "difficulty": "Hard" if avg_score < 5.5 else "Medium" if avg_score < 7.5 else "Easy"
            })
        
        return sorted(rankings, key=lambda q: q["avg_score"])[:10]  # Top 10 hardest
