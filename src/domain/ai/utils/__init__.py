"""
Utilitários de domínio para avaliação automática.
Algoritmos de divergência, consenso e validação.
"""

from .divergence_checker import DivergenceChecker
from .consensus_builder import ConsensusBuilder

__all__ = [
    "DivergenceChecker",
    "ConsensusBuilder",
]
