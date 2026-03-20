from __future__ import annotations

from typing import List

from src.domain.ai.agent_schemas import AgentCorrection

from src.core.settings import settings
from src.core.logging_config import get_logger


class DivergenceChecker:
    """
    Calcula divergência entre corretores independentes.
    
    Compara as notas totais de dois corretores e determina se a diferença
    excede o limiar configurado, sinalizando necessidade de árbitro.
    """
    
    def __init__(self, threshold: float = None) -> None:
        """
        Inicializa o checker com threshold customizado ou padrão.
        
        Args:
            threshold: Limiar de divergência. Se None, usa settings.DIVERGENCE_THRESHOLD
        """
        self.__threshold = threshold or settings.DIVERGENCE_THRESHOLD
        self.__logger = get_logger(__name__)
    
    def check_divergence(self, corrections: List[AgentCorrection]) -> dict:
        """
        Verifica se há divergência entre C1 e C2.
        
        Args:
            corrections: Lista com exatamente 2 correções (C1 e C2)
        
        Returns:
            {
                "is_divergent": bool,
                "difference": float,
                "threshold": float
            }
        
        Raises:
            AssertionError: Se não receber exatamente 2 correções
        """
        assert len(corrections) == 2, "Deve receber exatamente 2 correções"
        
        score1 = corrections[0].total_score
        score2 = corrections[1].total_score
        diff = abs(score1 - score2)
        
        is_divergent = diff > self.__threshold
        
        self.__logger.info(
            "Divergência: %.2f (threshold=%.2f) → Divergente? %s",
            diff, self.__threshold, is_divergent
        )
        
        return {
            "is_divergent": is_divergent,
            "difference": diff,
            "threshold": self.__threshold
        }
