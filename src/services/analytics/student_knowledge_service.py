"""
Servico de Base de Conhecimento do Aluno.
Rastreia lacunas de conhecimento por criterio ao longo do tempo.
"""
from __future__ import annotations

from typing import List

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class StudentKnowledgeService:
    """
    Rastreia gaps de conhecimento por aluno/criterio.
    Atualiza frequency quando o mesmo gap e detectado novamente.
    """

    async def extract_gaps_from_correction(
        self,
        correction_feedback: str,
        criteria_scores: List[dict],
        max_score_threshold: float = 0.5,
    ) -> List[dict]:
        """
        Extrai gaps de conhecimento a partir da correcao.

        Args:
            correction_feedback: Texto de feedback da correcao
            criteria_scores: Lista de {criterion, score, max_score, feedback}
            max_score_threshold: Criterios com score < threshold*max_score sao gaps

        Returns:
            Lista de {gap_description, criteria_name}
        """
        gaps = []
        for cs in criteria_scores:
            score = cs.get("score", 0)
            max_score = cs.get("max_score", 1) or 1

            if score < max_score * max_score_threshold:
                gap = {
                    "criteria_name": cs.get("criterion", "Desconhecido"),
                    "gap_description": cs.get("feedback")
                    or f"Desempenho insuficiente em: {cs.get('criterion', '')}",
                }
                gaps.append(gap)

        return gaps
