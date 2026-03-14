"""
Semantic Plagiarism Detector
Detects similar answers across students using TF-IDF + cosine similarity.
Conservative mode (default 90%+ threshold) to minimize false positives.
"""
import logging
import re
from dataclasses import dataclass, field

from src.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class PlagiarismMatch:
    """A detected plagiarism match between two students."""
    student_a_id: str
    student_a_name: str
    student_b_id: str
    student_b_name: str
    question_id: str
    similarity_score: float
    answer_a_preview: str
    answer_b_preview: str


@dataclass
class PlagiarismReport:
    """Full plagiarism report for a batch of submissions."""
    total_comparisons: int = 0
    flagged_pairs: list[PlagiarismMatch] = field(default_factory=list)
    threshold_used: float = 0.90

    @property
    def has_flags(self) -> bool:
        return len(self.flagged_pairs) > 0


def _normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip extra whitespace, remove punctuation."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def _preview(text: str, max_len: int = 100) -> str:
    """Create a preview of the text."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


class PlagiarismDetector:
    """
    Detects semantic similarity between student answers.

    Uses TF-IDF vectorization + cosine similarity (no external API calls).
    Conservative threshold (90%+ by default) to avoid false positives.
    """

    def __init__(self, threshold: float | None = None):
        self.threshold = threshold if threshold is not None else settings.PLAGIARISM_THRESHOLD

    def check_batch(
        self,
        submissions: list[dict],
    ) -> PlagiarismReport:
        """
        Check a batch of submissions for plagiarism.

        Args:
            submissions: List of dicts with keys:
                - student_id: str
                - student_name: str
                - question_id: str
                - answer: str

        Returns:
            PlagiarismReport with flagged pairs.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        report = PlagiarismReport(threshold_used=self.threshold)

        # Group by question
        by_question: dict[str, list[dict]] = {}
        for sub in submissions:
            q_id = sub["question_id"]
            if q_id not in by_question:
                by_question[q_id] = []
            by_question[q_id].append(sub)

        for q_id, q_submissions in by_question.items():
            if len(q_submissions) < 2:
                continue

            # Normalize texts
            texts = [_normalize_text(s["answer"]) for s in q_submissions]

            # Skip if any text is too short (< 20 words)
            valid_indices = [i for i, t in enumerate(texts) if len(t.split()) >= 20]
            if len(valid_indices) < 2:
                continue

            valid_subs = [q_submissions[i] for i in valid_indices]
            valid_texts = [texts[i] for i in valid_indices]

            # TF-IDF vectorization
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=5000,
                stop_words=None,  # Keep stop words for Portuguese
            )

            try:
                tfidf_matrix = vectorizer.fit_transform(valid_texts)
            except ValueError:
                continue

            # Pairwise cosine similarity
            sim_matrix = cosine_similarity(tfidf_matrix)

            # Check upper triangle (avoid duplicates)
            for i in range(len(valid_subs)):
                for j in range(i + 1, len(valid_subs)):
                    score = float(sim_matrix[i][j])
                    report.total_comparisons += 1

                    if score >= self.threshold:
                        match = PlagiarismMatch(
                            student_a_id=valid_subs[i]["student_id"],
                            student_a_name=valid_subs[i]["student_name"],
                            student_b_id=valid_subs[j]["student_id"],
                            student_b_name=valid_subs[j]["student_name"],
                            question_id=q_id,
                            similarity_score=score,
                            answer_a_preview=_preview(valid_subs[i]["answer"]),
                            answer_b_preview=_preview(valid_subs[j]["answer"]),
                        )
                        report.flagged_pairs.append(match)
                        logger.warning(
                            f"Plagiarism flag: {match.student_a_name} <-> {match.student_b_name} "
                            f"on {q_id} (similarity={score:.2%})"
                        )

        # Sort by similarity (highest first)
        report.flagged_pairs.sort(key=lambda m: m.similarity_score, reverse=True)
        return report
