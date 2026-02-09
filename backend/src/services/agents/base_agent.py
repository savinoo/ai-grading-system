"""
Interface abstrata para agentes corretores.
"""

from abc import ABC, abstractmethod
from src.domain.ai.agent_schemas import AgentCorrection


class BaseAgent(ABC):
    """
    Interface abstrata para agentes corretores.
    
    Todos os agentes (Examiners e Arbiter) devem implementar esta interface,
    garantindo consistência na chamada de métodos de avaliação/arbitragem.
    """
    
    @abstractmethod
    async def evaluate(self, **kwargs) -> AgentCorrection:
        """
        Método de avaliação/arbitragem.
        
        Cada agente implementa sua lógica específica:
        - ExaminerAgent: Avalia uma resposta de aluno
        - ArbiterAgent: Arbitra entre duas avaliações divergentes
        
        Args:
            **kwargs: Parâmetros específicos de cada implementação
        
        Returns:
            AgentCorrection: Resultado estruturado da avaliação
        
        Raises:
            NotImplementedError: Se o método não for implementado pela subclasse
        """
        raise NotImplementedError("Subclasses devem implementar o método evaluate")
