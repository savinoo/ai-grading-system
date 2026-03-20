from __future__ import annotations

from typing import List

from src.domain.ai.agent_schemas import AgentCorrection

from src.core.logging_config import get_logger


class ConsensusBuilder:
    """
    Calcula nota final baseada em consenso entre múltiplas avaliações.
    
    Estratégias:
    - 2 notas: média aritmética simples
    - 3 notas: média dos 2 corretores mais próximos (reduz outliers)
    """
    
    def __init__(self) -> None:
        """Inicializa o builder de consenso."""
        self.__logger = get_logger(__name__)
    
    def calculate_final_score(self, corrections: List[AgentCorrection]) -> float:
        """
        Calcula nota final baseada em consenso.
        
        Regras:
        - 2 notas: média simples (C1 + C2) / 2
        - 3 notas: média dos 2 mais próximos (descarta outlier)
        
        Args:
            corrections: Lista com 2 ou 3 correções
        
        Returns:
            Nota final consensuada
        
        Raises:
            ValueError: Se receber quantidade inválida de correções
        """
        scores = [c.total_score for c in corrections]
        
        if len(scores) == 2:
            final = sum(scores) / 2
            self.__logger.info(
                "Consenso (2 notas): média simples = %.2f",
                final
            )
            return final
        
        elif len(scores) == 3:
            # Ordenar e calcular distâncias entre notas adjacentes
            sorted_scores = sorted(scores)
            diff_low = sorted_scores[1] - sorted_scores[0]
            diff_high = sorted_scores[2] - sorted_scores[1]
            
            # Escolher o par mais próximo
            if diff_low < diff_high:
                # Notas mais próximas: 1ª e 2ª (descarta outlier alto)
                final = (sorted_scores[0] + sorted_scores[1]) / 2
            else:
                # Notas mais próximas: 2ª e 3ª (descarta outlier baixo)
                final = (sorted_scores[1] + sorted_scores[2]) / 2
            
            self.__logger.info(
                "Consenso (3 notas): %s → %.2f (descartou outlier)",
                sorted_scores, final
            )
            return final
        
        else:
            raise ValueError(
                f"Esperado 2 ou 3 correções, recebeu {len(scores)}"
            )
