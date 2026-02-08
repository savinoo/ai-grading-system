# 👨‍🏫 Professor Assistant Module

This module provides pedagogical intelligence on top of the grading workflow.

## Features

### 1. Student Performance Tracking (`student_tracker.py`)

Track individual student evolution over time:

```python
from src.analytics import StudentTracker
from src.domain.analytics_schemas import SubmissionRecord

tracker = StudentTracker()

# Add submission after grading
submission = SubmissionRecord(
    submission_id="SUB001",
    question_id="Q1",
    question_text="Explain X...",
    student_answer="Student's answer...",
    grade=7.5,
    max_score=10.0,
    criterion_scores={"Precisão": 7.0, "Clareza": 8.0}
)

profile = tracker.add_submission(
    student_id="S001",
    student_name="João Silva",
    submission=submission
)

# Access insights
print(f"Trend: {profile.trend}")  # "improving" | "stable" | "declining"
print(f"Learning Gaps: {profile.learning_gaps}")
print(f"Strengths: {profile.strengths}")
```

**Insights Generated:**
- **Trend Detection**: Uses linear regression to detect improvement/decline
- **Learning Gaps**: Criteria consistently scoring <60%
- **Strengths**: Criteria consistently scoring >80%
- **Confidence Scores**: R² values for trend predictions

---

### 2. Class-Level Analytics (`class_insights.py`)

Aggregate analysis for entire classes:

```python
from src.analytics import ClassAnalyzer

analyzer = ClassAnalyzer()
all_profiles = tracker.get_all_profiles()

insights = analyzer.analyze_class(
    class_id="CS101_2024",
    student_profiles=all_profiles
)

# Access class metrics
print(f"Class Average: {insights.class_avg_grade}")
print(f"Distribution: {insights.grade_distribution}")
print(f"Struggling Students: {insights.struggling_students}")
print(f"Common Gaps: {insights.most_common_gaps}")
```

**Insights Generated:**
- **Statistical Metrics**: Mean, median, std deviation
- **Grade Distribution**: A/B/C/D/F buckets
- **Outlier Detection**: Students >1σ from mean
- **Common Gaps**: Learning gaps affecting >30% of class
- **Question Difficulty**: Ranked by average scores

---

### 3. Persistent Memory (`memory/student_knowledge_base.py`)

Store student history across sessions:

```python
from src.memory import get_knowledge_base

kb = get_knowledge_base()

# Save profile
kb.add_or_update(profile)

# Retrieve later
loaded_profile = kb.get("S001")

# GDPR compliance
kb.delete("S001")  # Remove student data
kb.clear_old_submissions(days_to_keep=365)  # Cleanup old data
```

**Features:**
- JSON-based persistence (easy migration to SQL later)
- Automatic data retention policies
- Export functionality for reports
- GDPR-compliant deletion

---

## Data Models

### StudentProfile
```python
StudentProfile(
    student_id: str,
    student_name: str,
    submissions_history: List[SubmissionRecord],
    learning_gaps: List[LearningGap],
    strengths: List[Strength],
    avg_grade: float,
    trend: "improving" | "stable" | "declining",
    trend_confidence: float  # 0.0 to 1.0
)
```

### LearningGap
```python
LearningGap(
    criterion_name: str,
    topic: str,
    severity: "low" | "medium" | "high",
    evidence_count: int,
    avg_score: float,
    suggestion: str  # Actionable recommendation
)
```

### ClassInsights
```python
ClassInsights(
    class_id: str,
    total_students: int,
    class_avg_grade: float,
    grade_distribution: Dict[str, int],
    struggling_students: List[str],
    top_performers: List[str],
    most_common_gaps: List[LearningGap]
)
```

---

## Integration Example

See `examples/analytics_integration.py` for complete workflow integration.

Quick integration into existing workflow:

```python
# After running correction workflow
final_state = await workflow.ainvoke(inputs)

# Extract submission data
submission = SubmissionRecord(
    submission_id=f"SUB_{timestamp}",
    question_id=question.id,
    question_text=question.statement,
    student_answer=student_answer.text,
    grade=final_state["final_grade"],
    max_score=10.0,
    criterion_scores={...}  # Extract from corrections
)

# Track student
profile = tracker.add_submission(student_id, name, submission)

# Persist
kb.add_or_update(profile)
```

---

## Testing

Run analytics tests:

```bash
pytest tests/test_analytics.py -v
```

---

## Future Enhancements

- [ ] LLM-powered curriculum recommendations
- [ ] Visual dashboards with Plotly
- [ ] Semantic plagiarism detection
- [ ] Auto-generated study plans
- [ ] Predictive modeling (risk of failure)
- [ ] Teacher annotation system for agent training

---

## Storage

Profiles are stored in: `data/student_profiles.json`

To change storage location:
```python
kb = StudentKnowledgeBase(storage_path="custom/path.json")
```

For production, consider migrating to SQLite/PostgreSQL for better concurrency.
