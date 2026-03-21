"""
Servico de deteccao de plagio entre respostas de alunos.
Usa TF-IDF + cosine similarity para comparacao textual.
Threshold: 0.90 (configuravel via settings.PLAGIARISM_THRESHOLD)
"""
from __future__ import annotations

from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.core.settings import settings
from src.core.logging_config import get_logger

logger = get_logger("services")


class PlagiarismService:
    """
    Detecta plagio entre respostas de alunos usando TF-IDF + cosine similarity.

    Threshold padrao: 0.90 (configuravel via PLAGIARISM_THRESHOLD env var)
    """

    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            stop_words=None,  # Portugues nao tem lista nativa no sklearn
        )
        self._threshold = getattr(settings, "PLAGIARISM_THRESHOLD", 0.90)

    def detect(
        self,
        candidate_text: str,
        corpus_texts: List[str],
        corpus_ids: List[int],
    ) -> List[Tuple[int, float]]:
        """
        Verifica plagio entre candidate_text e corpus de respostas.

        Args:
            candidate_text: Resposta do aluno a verificar
            corpus_texts: Textos do corpus de comparacao
            corpus_ids: IDs correspondentes as respostas no corpus

        Returns:
            Lista de (answer_id, similarity_score) onde similarity >= threshold
        """
        if not corpus_texts:
            return []

        all_texts = [candidate_text] + corpus_texts

        try:
            tfidf_matrix = self._vectorizer.fit_transform(all_texts)
            candidate_vector = tfidf_matrix[0]
            corpus_matrix = tfidf_matrix[1:]

            similarities = cosine_similarity(
                candidate_vector, corpus_matrix
            ).flatten()

            results = []
            for idx, score in enumerate(similarities):
                if score >= self._threshold:
                    results.append((corpus_ids[idx], float(score)))
                    logger.warning(
                        "Plagiarism detected: similarity=%.3f with answer_id=%d",
                        score,
                        corpus_ids[idx],
                    )

            return sorted(results, key=lambda x: x[1], reverse=True)

        except Exception as e:
            logger.error("Plagiarism detection failed: %s", e)
            return []
