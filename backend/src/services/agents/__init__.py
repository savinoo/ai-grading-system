"""
Serviços de Agentes Corretores.

- ExaminerAgent: Corretor independente (usado 2x: C1 e C2)
- ArbiterAgent: Árbitro para desempate quando há divergência

Implementação via LangChain with_structured_output — 1 chamada LLM por correção.
"""

from src.services.agents.examiner_agent import ExaminerAgent
from src.services.agents.arbiter_agent import ArbiterAgent

__all__ = [
    "ExaminerAgent",
    "ArbiterAgent",
]
