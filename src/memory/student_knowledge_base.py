"""
Student Knowledge Base - Persistent Storage (SQLite Backend)
Stores student profiles and submission history across sessions.
Migrated from JSON to SQLite for academic robustness (Phase 2).
"""
import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from src.domain.analytics_schemas import (
    LearningGap,
    Strength,
    StudentProfile,
    SubmissionRecord,
)

logger = logging.getLogger(__name__)

DB_PATH_DEFAULT = "data/student_profiles.db"


class StudentKnowledgeBase:
    """
    Persistent storage for student learning profiles using SQLite.
    """

    def __init__(self, db_path: str = DB_PATH_DEFAULT):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()  # Protege writes concorrentes
        self._init_db()
        self._maybe_migrate_json()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_db(self):
        """Create tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                student_name TEXT NOT NULL,
                avg_grade REAL DEFAULT 0.0,
                submission_count INTEGER DEFAULT 0,
                trend TEXT DEFAULT 'insufficient_data',
                trend_confidence REAL DEFAULT 0.0,
                first_submission TEXT,
                last_submission TEXT,
                last_updated TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                submission_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                question_text TEXT NOT NULL,
                student_answer TEXT NOT NULL,
                grade REAL NOT NULL,
                max_score REAL NOT NULL,
                timestamp TEXT NOT NULL,
                criterion_scores TEXT DEFAULT '{}',
                divergence_detected INTEGER DEFAULT 0,
                feedback TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS learning_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                criterion_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                severity TEXT NOT NULL,
                evidence_count INTEGER NOT NULL,
                avg_score REAL NOT NULL,
                suggestion TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS strengths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                criterion_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                avg_score REAL NOT NULL,
                consistency REAL NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_submissions_student ON submissions(student_id);
            CREATE INDEX IF NOT EXISTS idx_submissions_timestamp ON submissions(timestamp);
            CREATE INDEX IF NOT EXISTS idx_gaps_student ON learning_gaps(student_id);
            CREATE INDEX IF NOT EXISTS idx_strengths_student ON strengths(student_id);
        """)
        self.conn.commit()

    def _maybe_migrate_json(self):
        """Auto-migrate from old JSON storage if it exists and DB is empty."""
        json_path = self.db_path.parent / "student_profiles.json"
        if not json_path.exists():
            return

        cursor = self.conn.execute("SELECT COUNT(*) FROM students")
        if cursor.fetchone()[0] > 0:
            return  # DB already has data

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            count = 0
            for student_id, profile_dict in data.items():
                profile = StudentProfile(**profile_dict)
                self._save_profile(profile)
                count += 1

            logger.info(f"Migrated {count} profiles from JSON to SQLite")

            # Rename old file as backup
            backup_path = json_path.with_suffix(".json.bak")
            json_path.rename(backup_path)
            logger.info(f"Old JSON file backed up to {backup_path}")
        except Exception as e:
            logger.error(f"JSON migration failed: {e}")

    def _save_profile(self, profile: StudentProfile):
        """Insert or replace a full profile into SQLite (thread-safe via lock)."""
        with self._lock:
            self._save_profile_unsafe(profile)
            self.conn.commit()

    def _save_profile_unsafe(self, profile: StudentProfile):
        """Internal write — must be called with self._lock held."""
        self.conn.execute(
            """INSERT OR REPLACE INTO students
               (student_id, student_name, avg_grade, submission_count, trend,
                trend_confidence, first_submission, last_submission, last_updated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                profile.student_id,
                profile.student_name,
                profile.avg_grade,
                profile.submission_count,
                profile.trend,
                profile.trend_confidence,
                profile.first_submission.isoformat() if profile.first_submission else None,
                profile.last_submission.isoformat() if profile.last_submission else None,
                profile.last_updated.isoformat(),
            ),
        )

        # Replace submissions
        self.conn.execute("DELETE FROM submissions WHERE student_id = ?", (profile.student_id,))
        for sub in profile.submissions_history:
            self.conn.execute(
                """INSERT INTO submissions
                   (student_id, submission_id, question_id, question_text, student_answer,
                    grade, max_score, timestamp, criterion_scores, divergence_detected, feedback)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile.student_id,
                    sub.submission_id,
                    sub.question_id,
                    sub.question_text,
                    sub.student_answer,
                    sub.grade,
                    sub.max_score,
                    sub.timestamp.isoformat(),
                    json.dumps(sub.criterion_scores),
                    int(sub.divergence_detected),
                    sub.feedback,
                ),
            )

        # Replace learning gaps
        self.conn.execute("DELETE FROM learning_gaps WHERE student_id = ?", (profile.student_id,))
        for gap in profile.learning_gaps:
            self.conn.execute(
                """INSERT INTO learning_gaps
                   (student_id, criterion_name, topic, severity, evidence_count, avg_score, suggestion)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile.student_id,
                    gap.criterion_name,
                    gap.topic,
                    gap.severity,
                    gap.evidence_count,
                    gap.avg_score,
                    gap.suggestion,
                ),
            )

        # Replace strengths
        self.conn.execute("DELETE FROM strengths WHERE student_id = ?", (profile.student_id,))
        for strength in profile.strengths:
            self.conn.execute(
                """INSERT INTO strengths
                   (student_id, criterion_name, topic, avg_score, consistency)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    profile.student_id,
                    strength.criterion_name,
                    strength.topic,
                    strength.avg_score,
                    strength.consistency,
                ),
            )
        # commit is done by _save_profile (the thread-safe wrapper)

    def _load_profile(self, row: sqlite3.Row) -> StudentProfile:
        """Reconstruct a StudentProfile from DB rows."""
        student_id = row["student_id"]

        # Load submissions
        submissions = []
        for sub_row in self.conn.execute(
            "SELECT * FROM submissions WHERE student_id = ? ORDER BY timestamp",
            (student_id,),
        ):
            submissions.append(
                SubmissionRecord(
                    submission_id=sub_row["submission_id"],
                    question_id=sub_row["question_id"],
                    question_text=sub_row["question_text"],
                    student_answer=sub_row["student_answer"],
                    grade=sub_row["grade"],
                    max_score=sub_row["max_score"],
                    timestamp=datetime.fromisoformat(sub_row["timestamp"]),
                    criterion_scores=json.loads(sub_row["criterion_scores"]),
                    divergence_detected=bool(sub_row["divergence_detected"]),
                    feedback=sub_row["feedback"],
                )
            )

        # Load gaps
        gaps = []
        for gap_row in self.conn.execute(
            "SELECT * FROM learning_gaps WHERE student_id = ?", (student_id,)
        ):
            gaps.append(
                LearningGap(
                    criterion_name=gap_row["criterion_name"],
                    topic=gap_row["topic"],
                    severity=gap_row["severity"],
                    evidence_count=gap_row["evidence_count"],
                    avg_score=gap_row["avg_score"],
                    suggestion=gap_row["suggestion"],
                )
            )

        # Load strengths
        strengths = []
        for str_row in self.conn.execute(
            "SELECT * FROM strengths WHERE student_id = ?", (student_id,)
        ):
            strengths.append(
                Strength(
                    criterion_name=str_row["criterion_name"],
                    topic=str_row["topic"],
                    avg_score=str_row["avg_score"],
                    consistency=str_row["consistency"],
                )
            )

        return StudentProfile(
            student_id=row["student_id"],
            student_name=row["student_name"],
            submissions_history=submissions,
            learning_gaps=gaps,
            strengths=strengths,
            avg_grade=row["avg_grade"],
            submission_count=row["submission_count"],
            trend=row["trend"],
            trend_confidence=row["trend_confidence"],
            first_submission=datetime.fromisoformat(row["first_submission"]) if row["first_submission"] else None,
            last_submission=datetime.fromisoformat(row["last_submission"]) if row["last_submission"] else None,
            last_updated=datetime.fromisoformat(row["last_updated"]),
        )

    def add_or_update(self, profile: StudentProfile):
        """Add new profile or update existing."""
        self._save_profile(profile)

    def get(self, student_id: str) -> StudentProfile | None:
        """Retrieve student profile."""
        row = self.conn.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        if row is None:
            return None
        return self._load_profile(row)

    def get_all(self) -> list[StudentProfile]:
        """Get all profiles."""
        rows = self.conn.execute("SELECT * FROM students").fetchall()
        return [self._load_profile(row) for row in rows]

    def delete(self, student_id: str):
        """Remove student profile (GDPR compliance). CASCADE deletes related data."""
        self.conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        self.conn.commit()
        logger.info(f"Deleted profile for {student_id}")

    def export_student_history(self, student_id: str, output_path: str):
        """Export single student's complete history as JSON."""
        profile = self.get(student_id)
        if not profile:
            logger.warning(f"No profile found for {student_id}")
            return

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(profile.model_dump(mode="json"), f, indent=2, default=str)

        logger.info(f"Exported {student_id} history to {output}")

    def export_and_anonymize(self, student_id: str, output_path: str):
        """
        GDPR: Export student data in anonymized form, then delete original.
        Replaces identifying info with hashed placeholders.
        """
        import hashlib

        profile = self.get(student_id)
        if not profile:
            logger.warning(f"No profile found for {student_id}")
            return

        # Anonymize
        anon_id = hashlib.sha256(student_id.encode()).hexdigest()[:12]
        data = profile.model_dump(mode="json")
        data["student_id"] = f"ANON-{anon_id}"
        data["student_name"] = f"Anonimizado-{anon_id[:6]}"

        # Anonymize answers (may contain personal info)
        for sub in data.get("submissions_history", []):
            sub["student_answer"] = "[ANONYMIZED]"

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)

        # Delete original
        self.delete(student_id)
        logger.info(f"Exported anonymized data for {student_id} to {output}, original deleted")

    def clear_old_submissions(self, days_to_keep: int = 365):
        """
        Remove submissions older than specified days.
        For privacy compliance and storage management.
        """
        from datetime import timedelta

        cutoff = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        cursor = self.conn.execute(
            "DELETE FROM submissions WHERE timestamp < ?", (cutoff,)
        )
        removed = cursor.rowcount
        self.conn.commit()

        if removed > 0:
            logger.info(f"Removed {removed} old submissions (older than {days_to_keep} days)")

        return removed

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# Global instance
_global_kb: StudentKnowledgeBase | None = None


def get_knowledge_base() -> StudentKnowledgeBase:
    """Get or create global knowledge base instance."""
    global _global_kb
    if _global_kb is None:
        _global_kb = StudentKnowledgeBase()
    return _global_kb
