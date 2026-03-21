"""
Serviços de Agentes Corretores com DSPy.

Este módulo fornece implementações de agentes para correção automática:
- ExaminerAgent: Corretor independente (usado 2x: C1 e C2)
- ArbiterAgent: Árbitro para desempate quando há divergência
"""

from src.services.agents.examiner_agent import ExaminerAgent
from src.services.agents.arbiter_agent import ArbiterAgent

__all__ = [
    "ExaminerAgent",
    "ArbiterAgent",
]

__all__ = [
    "BaseAgent",
    "ExaminerAgent",
    "ArbiterAgent",
    "CORRECTOR_SYSTEM_PROMPT",
    "ARBITER_SYSTEM_PROMPT",
    "format_rubric_text",
    "format_rag_context",
]
