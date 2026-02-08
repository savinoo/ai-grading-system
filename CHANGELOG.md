# Changelog - AI Grading System

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-02-08

### Added - Professor Assistant Module ✨

#### Core Analytics Features
- **Student Tracking System** (`src/analytics/student_tracker.py`)
  - Individual student performance tracking over time
  - Learning gap identification (criteria where student consistently scores <60%)
  - Strength recognition (criteria with avg >8.0)
  - Trend detection using linear regression (improving/stable/declining)
  - Confidence scoring for trend predictions

- **Class-Level Insights** (`src/analytics/class_insights.py`)
  - Aggregate class performance metrics (avg, median, std deviation)
  - Grade distribution (A/B/C/D/F buckets)
  - Outlier detection (struggling students and top performers)
  - Common learning gaps across 30%+ of class
  - Question difficulty ranking based on average scores

- **Persistent Memory** (`src/memory/student_knowledge_base.py`)
  - JSON-based storage for student profiles
  - Submission history preservation across sessions
  - GDPR-compliant data deletion
  - Automatic cleanup of old submissions (365-day default)
  - Export functionality for individual student reports

#### New Data Models
- **Analytics Schemas** (`src/domain/analytics_schemas.py`)
  - `StudentProfile`: Complete learning profile with submission history
  - `SubmissionRecord`: Individual correction data point
  - `LearningGap`: Identified weakness with severity classification
  - `Strength`: Recognized strong areas with consistency metrics
  - `ClassInsights`: Aggregated class-level analytics
  - `TeacherAnnotation`: Feedback capture for agent training

### Enhanced
- **Architecture Documentation**
  - Created `ANALYSIS.md` with current state assessment
  - Documented Phase 1-3 enhancement roadmap
  - Added technical debt and improvement notes

### Dependencies to Add
```txt
numpy>=1.24.0
scipy>=1.10.0
plotly>=5.0.0  # For future dashboard visualizations
```

### TODO - Next Steps
- [ ] Integrate analytics into Streamlit UI
- [ ] Add visual dashboards (Plotly charts)
- [ ] Implement semantic plagiarism detection
- [ ] Add LLM-based curriculum intelligence agent
- [ ] Create auto-generated study plan feature
- [ ] Add unit tests for analytics modules
- [ ] Update requirements.txt

### Technical Notes
- All analytics modules are **non-breaking additions**
- Existing LangGraph workflow remains unchanged
- Analytics run as post-processing step
- Storage uses JSON (can migrate to SQLite/PostgreSQL in Phase 2)

---

## [Previous] - Before 2026-02-08

### Existing Features
- Multi-agent grading workflow (Examiner C1, C2, Arbiter)
- LangGraph orchestration with conditional routing
- RAG system with ChromaDB
- Streamlit interface (single + batch modes)
- Mock data generation for testing
- LangSmith observability integration
- Structured output with Pydantic schemas
- Retry logic with Tenacity
- Batch processing with rate limit handling
