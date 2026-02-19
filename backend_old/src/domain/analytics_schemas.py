"""
Analytics Schemas for Professor Assistant Module
Tracks student performance, learning gaps, and class-level insights.
"""
from datetime import datetime
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class SubmissionRecord(BaseModel):
    """Individual submission data point"""
    submission_id: str
    question_id: str
    question_text: str
    student_answer: str
    grade: float
    max_score: float
    timestamp: datetime = Field(default_factory=datetime.now)
    criterion_scores: Dict[str, float] = Field(default_factory=dict)
    divergence_detected: bool = False
    feedback: Optional[str] = None


class LearningGap(BaseModel):
    """Identified weakness in student understanding"""
    criterion_name: str
    topic: str
    severity: Literal["low", "medium", "high"]
    evidence_count: int  # How many times this appeared
    avg_score: float
    suggestion: Optional[str] = None


class Strength(BaseModel):
    """Identified strong area for student"""
    criterion_name: str
    topic: str
    avg_score: float
    consistency: float  # 0-1, how consistently they score well


class StudentProfile(BaseModel):
    """Complete student learning profile"""
    student_id: str
    student_name: str
    submissions_history: List[SubmissionRecord] = Field(default_factory=list)
    learning_gaps: List[LearningGap] = Field(default_factory=list)
    strengths: List[Strength] = Field(default_factory=list)
    
    # Computed metrics
    avg_grade: float = 0.0
    submission_count: int = 0
    trend: Literal["improving", "stable", "declining", "insufficient_data"] = "insufficient_data"
    trend_confidence: float = 0.0
    
    # Metadata
    first_submission: Optional[datetime] = None
    last_submission: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class ClassInsights(BaseModel):
    """Aggregated class-level analytics"""
    class_id: str
    total_students: int
    total_submissions: int
    
    # Performance metrics
    class_avg_grade: float
    median_grade: float
    std_deviation: float
    
    # Distribution
    grade_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Buckets: A (9-10), B (7-9), C (5-7), D (3-5), F (<3)"
    )
    
    # Common patterns
    most_difficult_questions: List[Dict[str, Any]] = Field(default_factory=list)
    most_common_gaps: List[LearningGap] = Field(default_factory=list)
    
    # Outliers
    struggling_students: List[str] = Field(
        default_factory=list,
        description="Students scoring >1 std dev below mean"
    )
    top_performers: List[str] = Field(
        default_factory=list,
        description="Students scoring >1 std dev above mean"
    )
    
    # Temporal
    analysis_timestamp: datetime = Field(default_factory=datetime.now)


class TeacherAnnotation(BaseModel):
    """Teacher feedback on agent corrections"""
    annotation_id: str
    submission_id: str
    agent_grade: float
    teacher_grade: Optional[float] = None
    agreement: Literal["agree", "disagree", "partial"] = "agree"
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
