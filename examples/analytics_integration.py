"""
Example: How to integrate analytics into the existing workflow
This shows how to track students and generate insights after corrections.
"""
import asyncio
from datetime import datetime

# Existing imports
from src.workflow.graph import build_grading_workflow
from src.domain.schemas import ExamQuestion, EvaluationCriterion, QuestionMetadata, StudentAnswer

# New imports
from src.analytics import StudentTracker, ClassAnalyzer
from src.domain.analytics_schemas import SubmissionRecord
from src.memory import get_knowledge_base


async def example_workflow_with_analytics():
    """
    Example of how to run corrections and track analytics.
    """
    
    # 1. Setup (existing)
    workflow = build_grading_workflow()
    tracker = StudentTracker()
    kb = get_knowledge_base()
    
    # 2. Prepare question (existing)
    question = ExamQuestion(
        id="Q1",
        statement="Explain the difference between B-Trees and B+ Trees",
        rubric=[
            EvaluationCriterion(
                name="Precisão",
                description="Correctness of concepts",
                weight=6,
                max_score=6
            ),
            EvaluationCriterion(
                name="Clareza",
                description="Clarity of explanation",
                weight=4,
                max_score=4
            )
        ],
        metadata=QuestionMetadata(
            discipline="Computer Science",
            topic="Data Structures"
        )
    )
    
    # 3. Student answer (existing)
    student_answer = StudentAnswer(
        student_id="S001",
        question_id="Q1",
        text="B-Trees store data in all nodes, while B+ Trees only store data in leaf nodes..."
    )
    
    # 4. Run correction (existing workflow)
    inputs = {
        "question": question,
        "student_answer": student_answer,
        "rag_context": [],
        "individual_corrections": []
    }
    
    final_state = await workflow.ainvoke(inputs)
    
    # 5. **NEW**: Extract analytics data
    submission_record = SubmissionRecord(
        submission_id=f"SUB_{datetime.now().timestamp()}",
        question_id=question.id,
        question_text=question.statement,
        student_answer=student_answer.text,
        grade=final_state["final_grade"],
        max_score=10.0,
        timestamp=datetime.now(),
        criterion_scores={
            # Extract from individual_corrections
            corr.criterion_name: corr.score
            for corr in final_state["individual_corrections"][-1].criterion_scores
        },
        divergence_detected=final_state["divergence_detected"]
    )
    
    # 6. **NEW**: Update student profile
    profile = tracker.add_submission(
        student_id="S001",
        student_name="João Silva",
        submission=submission_record
    )
    
    # 7. **NEW**: Save to persistent storage
    kb.add_or_update(profile)
    
    # 8. **NEW**: Generate insights
    print(f"\n=== Student Profile ===")
    print(f"Name: {profile.student_name}")
    print(f"Average Grade: {profile.avg_grade:.2f}")
    print(f"Trend: {profile.trend} (confidence: {profile.trend_confidence:.2f})")
    
    print(f"\n=== Learning Gaps ===")
    for gap in profile.learning_gaps:
        print(f"- {gap.criterion_name}: {gap.avg_score:.2f} ({gap.severity} severity)")
        print(f"  Suggestion: {gap.suggestion}")
    
    print(f"\n=== Strengths ===")
    for strength in profile.strengths:
        print(f"- {strength.criterion_name}: {strength.avg_score:.2f}")
    
    return profile


async def example_class_analytics():
    """
    Example of generating class-level insights.
    """
    
    kb = get_knowledge_base()
    analyzer = ClassAnalyzer()
    
    # Get all student profiles
    all_profiles = kb.get_all()
    
    # Generate class insights
    insights = analyzer.analyze_class(
        class_id="CS101_2024",
        student_profiles=all_profiles
    )
    
    print(f"\n=== Class Insights ===")
    print(f"Total Students: {insights.total_students}")
    print(f"Total Submissions: {insights.total_submissions}")
    print(f"Class Average: {insights.class_avg_grade:.2f}")
    print(f"Median: {insights.median_grade:.2f}")
    print(f"Std Deviation: {insights.std_deviation:.2f}")
    
    print(f"\n=== Grade Distribution ===")
    for grade, count in insights.grade_distribution.items():
        print(f"{grade}: {count} students")
    
    print(f"\n=== Struggling Students ===")
    for name in insights.struggling_students:
        print(f"- {name}")
    
    print(f"\n=== Top Performers ===")
    for name in insights.top_performers:
        print(f"- {name}")
    
    print(f"\n=== Common Learning Gaps ===")
    for gap in insights.most_common_gaps:
        print(f"- {gap.criterion_name}: {gap.evidence_count} students affected")
        print(f"  Avg Score: {gap.avg_score:.2f}")
        print(f"  Suggestion: {gap.suggestion}")
    
    return insights


if __name__ == "__main__":
    # Run examples
    print("Running student analytics example...")
    asyncio.run(example_workflow_with_analytics())
    
    print("\n" + "="*60 + "\n")
    
    print("Running class analytics example...")
    asyncio.run(example_class_analytics())
