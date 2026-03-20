"""
Domínio AI/RAG: schemas, prompts, utils e workflows.
Centraliza DTOs, lógica de negócio e orquestração de avaliação automática.
"""

from .schemas import *  # noqa: F403
from .agent_schemas import *  # noqa: F403
from .rag_schemas import *  # noqa: F403

# Workflows e utilitários de domínio
from .utils.divergence_checker import DivergenceChecker
from .utils.consensus_builder import ConsensusBuilder


def get_grading_graph(*args, **kwargs):
    from .workflow.graph import get_grading_graph as _get_grading_graph

    return _get_grading_graph(*args, **kwargs)

__all__ = [
    "get_grading_graph",
    "DivergenceChecker",
    "ConsensusBuilder",
]
