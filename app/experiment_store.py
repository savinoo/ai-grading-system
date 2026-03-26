"""
ExperimentStore — Persistent storage for TCC experiment results.

Captures EVERY data point from each experiment run in a structured SQLite database:
- Experiment metadata (config, provider, model, timestamps)
- Questions generated (statement, rubric, discipline)
- Student answers (text, quality profile)
- Corrections (C1, C2, Arbiter — scores, reasoning, feedback, criterion scores)
- RAG contexts (chunks, relevance scores, sources)
- Divergence data (detected, value, threshold)
- Final scores (consensus method, all scores)

Usage:
    store = get_experiment_store()
    exp_id = store.create_experiment(config={...})
    store.save_question(exp_id, question)
    store.save_answer(exp_id, question_id, student, answer)
    store.save_correction(exp_id, question_id, student_id, correction, agent_role)
    store.save_result(exp_id, question_id, student_id, final_state)
    store.export_experiment(exp_id, "tcc/results/exp_001.json")
"""
import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from uuid import UUID

logger = logging.getLogger("experiment_store")

DB_PATH = "data/experiments.db"


def _serialize(obj):
    """Convert objects to JSON-safe types."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, 'model_dump'):
        return obj.model_dump(mode="json")
    return str(obj)


class ExperimentStore:
    """SQLite-backed storage for TCC experiment data."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
        self._lock = threading.Lock()
        self._init_db()

    @property
    def conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT DEFAULT 'running',
                llm_provider TEXT,
                llm_model TEXT,
                num_questions INTEGER,
                num_students INTEGER,
                divergence_threshold REAL,
                discipline TEXT,
                topic TEXT,
                config_json TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS experiment_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                question_uuid TEXT NOT NULL,
                statement TEXT NOT NULL,
                total_points REAL DEFAULT 10.0,
                rubric_json TEXT DEFAULT '[]',
                discipline TEXT,
                topic TEXT,
                difficulty TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS experiment_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                quality_profile TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS experiment_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                question_uuid TEXT NOT NULL,
                student_id TEXT NOT NULL,
                student_name TEXT,
                quality_actual TEXT,
                answer_text TEXT NOT NULL,
                generated_at TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS experiment_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                question_uuid TEXT NOT NULL,
                student_id TEXT NOT NULL,
                agent_role TEXT NOT NULL,
                total_score REAL,
                reasoning_chain TEXT,
                feedback_text TEXT,
                confidence_level REAL,
                criterion_scores_json TEXT DEFAULT '[]',
                created_at TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS experiment_rag_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                question_uuid TEXT NOT NULL,
                student_id TEXT NOT NULL,
                chunk_content TEXT,
                relevance_score REAL,
                source_document TEXT,
                page_number INTEGER,
                chunk_index INTEGER,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS experiment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                question_uuid TEXT NOT NULL,
                student_id TEXT NOT NULL,
                c1_score REAL,
                c2_score REAL,
                arbiter_score REAL,
                divergence_detected INTEGER DEFAULT 0,
                divergence_value REAL DEFAULT 0.0,
                final_score REAL,
                consensus_method TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_eq_exp ON experiment_questions(experiment_id);
            CREATE INDEX IF NOT EXISTS idx_ea_exp ON experiment_answers(experiment_id);
            CREATE INDEX IF NOT EXISTS idx_ec_exp ON experiment_corrections(experiment_id);
            CREATE INDEX IF NOT EXISTS idx_er_exp ON experiment_results(experiment_id);
            CREATE INDEX IF NOT EXISTS idx_erag_exp ON experiment_rag_contexts(experiment_id);
        """)
        self.conn.commit()
        logger.info(f"ExperimentStore initialized at {self.db_path}")

    # ─── Create Experiment ───

    def create_experiment(self, config: dict) -> int:
        """Create a new experiment run and return its ID."""
        with self._lock:
            cursor = self.conn.execute(
                """INSERT INTO experiments
                   (created_at, llm_provider, llm_model, num_questions, num_students,
                    divergence_threshold, discipline, topic, config_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(),
                    config.get('llm_provider'),
                    config.get('llm_model'),
                    config.get('num_questions'),
                    config.get('num_students'),
                    config.get('divergence_threshold'),
                    config.get('discipline'),
                    config.get('topic'),
                    json.dumps(config, default=str, ensure_ascii=False),
                )
            )
            self.conn.commit()
            exp_id = cursor.lastrowid
            logger.info(f"[EXP-{exp_id}] Experiment created")
            return exp_id

    def finish_experiment(self, exp_id: int, status: str = "completed"):
        """Mark experiment as finished."""
        with self._lock:
            self.conn.execute(
                "UPDATE experiments SET finished_at = ?, status = ? WHERE id = ?",
                (datetime.now().isoformat(), status, exp_id)
            )
            self.conn.commit()

    # ─── Save Questions ───

    def save_question(self, exp_id: int, question):
        """Save a generated question."""
        rubric = []
        if hasattr(question, 'rubric') and question.rubric:
            rubric = [r.model_dump(mode="json") if hasattr(r, 'model_dump') else r for r in question.rubric]

        metadata = question.metadata if hasattr(question, 'metadata') else None

        with self._lock:
            self.conn.execute(
                """INSERT INTO experiment_questions
                   (experiment_id, question_uuid, statement, total_points, rubric_json,
                    discipline, topic, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    exp_id,
                    str(question.id),
                    question.statement,
                    getattr(question, 'total_points', 10.0),
                    json.dumps(rubric, ensure_ascii=False, default=str),
                    metadata.discipline if metadata else None,
                    metadata.topic if metadata else None,
                    metadata.difficulty_level if metadata else None,
                )
            )
            self.conn.commit()

    def save_questions(self, exp_id: int, questions: list):
        """Save multiple questions."""
        for q in questions:
            self.save_question(exp_id, q)

    # ─── Save Students ───

    def save_student(self, exp_id: int, student: dict):
        """Save a student profile."""
        with self._lock:
            self.conn.execute(
                """INSERT INTO experiment_students
                   (experiment_id, student_id, student_name, quality_profile)
                   VALUES (?, ?, ?, ?)""",
                (exp_id, str(student['id']), student['name'], student.get('quality'))
            )
            self.conn.commit()

    def save_students(self, exp_id: int, students: list):
        """Save multiple students."""
        for s in students:
            self.save_student(exp_id, s)

    # ─── Save Answers ───

    def save_answer(self, exp_id: int, question_uuid, student_id, student_name,
                    answer_text, quality_actual=None):
        """Save a student answer."""
        with self._lock:
            self.conn.execute(
                """INSERT INTO experiment_answers
                   (experiment_id, question_uuid, student_id, student_name,
                    quality_actual, answer_text, generated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    exp_id, str(question_uuid), str(student_id), student_name,
                    quality_actual, answer_text, datetime.now().isoformat()
                )
            )
            self.conn.commit()

    # ─── Save Corrections ───

    def save_correction(self, exp_id: int, question_uuid, student_id, correction, agent_role: str):
        """Save an agent correction (C1, C2, or Arbiter)."""
        if correction is None:
            return

        criterion_scores = []
        if hasattr(correction, 'criterion_scores') and correction.criterion_scores:
            criterion_scores = [
                cs.model_dump(mode="json") if hasattr(cs, 'model_dump') else cs
                for cs in correction.criterion_scores
            ]

        with self._lock:
            self.conn.execute(
                """INSERT INTO experiment_corrections
                   (experiment_id, question_uuid, student_id, agent_role,
                    total_score, reasoning_chain, feedback_text, confidence_level,
                    criterion_scores_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    exp_id, str(question_uuid), str(student_id), agent_role,
                    correction.total_score,
                    correction.reasoning_chain,
                    correction.feedback_text,
                    getattr(correction, 'confidence_level', None),
                    json.dumps(criterion_scores, ensure_ascii=False, default=str),
                    datetime.now().isoformat(),
                )
            )
            self.conn.commit()

    # ─── Save RAG Contexts ───

    def save_rag_contexts(self, exp_id: int, question_uuid, student_id, contexts: list):
        """Save RAG contexts used for a correction."""
        if not contexts:
            return

        with self._lock:
            for ctx in contexts:
                self.conn.execute(
                    """INSERT INTO experiment_rag_contexts
                       (experiment_id, question_uuid, student_id, chunk_content,
                        relevance_score, source_document, page_number, chunk_index)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        exp_id, str(question_uuid), str(student_id),
                        ctx.content if hasattr(ctx, 'content') else str(ctx),
                        getattr(ctx, 'relevance_score', None),
                        getattr(ctx, 'source_document', None),
                        getattr(ctx, 'page_number', None),
                        getattr(ctx, 'chunk_index', None),
                    )
                )
            self.conn.commit()

    # ─── Save Final Result ───

    def save_result(self, exp_id: int, question_uuid, student_id, final_state: dict):
        """Save the final result for a question/student pair."""
        c1 = final_state.get('correction_1')
        c2 = final_state.get('correction_2')
        arb = final_state.get('correction_arbiter')
        divergence = final_state.get('divergence_detected', False)
        div_value = final_state.get('divergence_value', 0.0)
        final_score = final_state.get('final_score')

        if arb:
            consensus = "closest_pair_3"
        else:
            consensus = "mean_2"

        with self._lock:
            self.conn.execute(
                """INSERT INTO experiment_results
                   (experiment_id, question_uuid, student_id, c1_score, c2_score,
                    arbiter_score, divergence_detected, divergence_value,
                    final_score, consensus_method)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    exp_id, str(question_uuid), str(student_id),
                    c1.total_score if c1 else None,
                    c2.total_score if c2 else None,
                    arb.total_score if arb else None,
                    int(divergence),
                    div_value,
                    final_score,
                    consensus,
                )
            )
            self.conn.commit()

    # ─── Save Complete Pipeline State ───

    def save_pipeline_state(self, exp_id: int, question_uuid, student_id,
                            student_name, final_state: dict):
        """Save everything from a completed pipeline run in one call."""
        # Corrections
        self.save_correction(exp_id, question_uuid, student_id,
                             final_state.get('correction_1'), 'corretor_1')
        self.save_correction(exp_id, question_uuid, student_id,
                             final_state.get('correction_2'), 'corretor_2')
        self.save_correction(exp_id, question_uuid, student_id,
                             final_state.get('correction_arbiter'), 'arbiter')

        # RAG
        self.save_rag_contexts(exp_id, question_uuid, student_id,
                               final_state.get('rag_contexts') or [])

        # Final result
        self.save_result(exp_id, question_uuid, student_id, final_state)

    # ─── Export ───

    def export_experiment(self, exp_id: int, output_path: str = None) -> dict:
        """Export complete experiment data as JSON."""
        exp = dict(self.conn.execute(
            "SELECT * FROM experiments WHERE id = ?", (exp_id,)
        ).fetchone())

        exp['questions'] = [dict(r) for r in self.conn.execute(
            "SELECT * FROM experiment_questions WHERE experiment_id = ?", (exp_id,)
        ).fetchall()]

        exp['students'] = [dict(r) for r in self.conn.execute(
            "SELECT * FROM experiment_students WHERE experiment_id = ?", (exp_id,)
        ).fetchall()]

        exp['answers'] = [dict(r) for r in self.conn.execute(
            "SELECT * FROM experiment_answers WHERE experiment_id = ?", (exp_id,)
        ).fetchall()]

        exp['corrections'] = [dict(r) for r in self.conn.execute(
            "SELECT * FROM experiment_corrections WHERE experiment_id = ?", (exp_id,)
        ).fetchall()]

        # Parse criterion_scores_json back to lists
        for c in exp['corrections']:
            try:
                c['criterion_scores'] = json.loads(c.pop('criterion_scores_json', '[]'))
            except (json.JSONDecodeError, TypeError):
                c['criterion_scores'] = []

        exp['rag_contexts'] = [dict(r) for r in self.conn.execute(
            "SELECT * FROM experiment_rag_contexts WHERE experiment_id = ?", (exp_id,)
        ).fetchall()]

        exp['results'] = [dict(r) for r in self.conn.execute(
            "SELECT * FROM experiment_results WHERE experiment_id = ?", (exp_id,)
        ).fetchall()]

        # Parse config
        try:
            exp['config'] = json.loads(exp.pop('config_json', '{}'))
        except (json.JSONDecodeError, TypeError):
            exp['config'] = {}

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(exp, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"[EXP-{exp_id}] Exported to {output_path}")

        return exp

    def list_experiments(self) -> list:
        """List all experiments."""
        rows = self.conn.execute(
            "SELECT id, created_at, status, llm_model, num_questions, num_students, discipline FROM experiments ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_results_dataframe(self, exp_id: int):
        """Get results as a list of dicts (for pandas DataFrame)."""
        rows = self.conn.execute("""
            SELECT
                er.question_uuid, eq.statement as question_text,
                er.student_id, es.student_name, es.quality_profile,
                er.c1_score, er.c2_score, er.arbiter_score,
                er.divergence_detected, er.divergence_value,
                er.final_score, er.consensus_method
            FROM experiment_results er
            LEFT JOIN experiment_questions eq ON er.question_uuid = eq.question_uuid AND er.experiment_id = eq.experiment_id
            LEFT JOIN experiment_students es ON er.student_id = es.student_id AND er.experiment_id = es.experiment_id
            WHERE er.experiment_id = ?
            ORDER BY eq.id, es.id
        """, (exp_id,)).fetchall()
        return [dict(r) for r in rows]

    # ─── Load for Reuse ───

    def load_questions(self, exp_id: int) -> list:
        """Load questions from a previous experiment for reuse."""
        rows = self.conn.execute(
            "SELECT question_uuid, statement, total_points, rubric_json, discipline, topic, difficulty "
            "FROM experiment_questions WHERE experiment_id = ? ORDER BY id",
            (exp_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def load_students(self, exp_id: int) -> list:
        """Load students from a previous experiment for reuse."""
        rows = self.conn.execute(
            "SELECT student_id, student_name, quality_profile "
            "FROM experiment_students WHERE experiment_id = ? ORDER BY id",
            (exp_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def load_answers(self, exp_id: int) -> list:
        """Load answers from a previous experiment for reuse."""
        rows = self.conn.execute(
            "SELECT question_uuid, student_id, student_name, quality_actual, answer_text "
            "FROM experiment_answers WHERE experiment_id = ? ORDER BY id",
            (exp_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_experiment(self, exp_id: int) -> dict:
        """Get experiment metadata."""
        row = self.conn.execute(
            "SELECT * FROM experiments WHERE id = ?", (exp_id,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        try:
            result['config'] = json.loads(result.pop('config_json', '{}'))
        except (json.JSONDecodeError, TypeError):
            result['config'] = {}
        return result

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# Global instance
_store = None


def get_experiment_store() -> ExperimentStore:
    global _store
    if _store is None:
        _store = ExperimentStore()
    return _store
