"""
Workflow LangGraph para correção automática.
Define estado, nodes e grafo de execução.
"""

from .state import GradingState
from .graph import get_grading_graph, create_grading_graph

__all__ = [
    "GradingState",
    "get_grading_graph",
    "create_grading_graph",
]
