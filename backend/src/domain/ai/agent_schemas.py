"""
Schemas específicos para agentes corretores (DSPy Signatures).
Define estruturas de saída dos agentes e tipos de correção.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class AgentID(str, Enum):
    """
    Identificadores únicos dos agentes no sistema multi-agent.
    
    - CORRETOR_1: Primeiro avaliador independente
    - CORRETOR_2: Segundo avaliador independente
    - ARBITER: Árbitro que resolve divergências
    """
    
    CORRETOR_1 = "corretor_1"
    CORRETOR_2 = "corretor_2"
    ARBITER = "corretor_3_arbiter"


class CriterionScore(BaseModel):
    """
    Score individual de um critério de avaliação.
    Permite rastreamento granular da nota por aspecto.
    """
    
    criterion: str = Field(
        ...,
        description="Nome do critério avaliado",
        min_length=1
    )
    score: float = Field(
        ...,
        description="Pontuação obtida neste critério",
        ge=0.0
    )
    max_score: Optional[float] = Field(
        default=None,
        description="Pontuação máxima possível neste critério"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Feedback específico sobre este critério"
    )
    
    @field_validator('score')
    @classmethod
    def validate_score_not_exceeds_max(cls, v: float) -> float:
        """Clamp defensivo: garante score >= 0."""
        if v < 0:
            return 0.0
        return v


class AgentCorrection(BaseModel):
    """
    Saída estruturada de um agente corretor (DSPy output).
    
    Força o modelo a gerar raciocínio Chain-of-Thought ANTES da nota,
    garantindo avaliações mais consistentes e explicáveis.
    """
    
    agent_id: Optional[AgentID] = Field(
        default=None,
        description="Identificador do agente que gerou esta correção"
    )
    
    reasoning_chain: str = Field(
        ...,
        description=(
            "Chain-of-Thought (CoT): OBRIGATÓRIO. "
            "Raciocínio passo-a-passo ANTES de atribuir a nota. "
            "Deve analisar a resposta contra cada critério da rubrica."
        ),
        min_length=50
    )
    
    criteria_scores: List[CriterionScore] = Field(
        default_factory=list,
        description="Lista de scores por critério avaliado"
    )
    
    total_score: Optional[float] = Field(
        default=None,
        description="Nota total calculada (soma ponderada dos critérios)",
        ge=0.0
    )
    
    feedback_text: str = Field(
        default="Feedback não gerado.",
        description="Feedback pedagógico consolidado para o aluno"
    )
    
    # Metadados de tracking
    confidence_level: Optional[float] = Field(
        default=None,
        description="Nível de confiança do agente (0.0 a 1.0)",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        """Configuração Pydantic."""
        use_enum_values = True
    
    @field_validator('reasoning_chain', mode='before')
    @classmethod
    def coerce_reasoning_chain(cls, v) -> str:
        """Converte lista de strings em string única, se necessário."""
        if isinstance(v, list):
            return ' '.join(str(item) for item in v)
        return str(v) if v is not None else ''
    
    @field_validator('criteria_scores', mode='before')
    @classmethod
    def coerce_criteria_scores(cls, v):
        """Converte dict único em lista com um elemento, se necessário."""
        if isinstance(v, dict):
            return [v]
        if v is None:
            return []
        return v
    
    @field_validator('total_score', mode='before')
    @classmethod
    def check_score_range(cls, v) -> Optional[float]:
        """Clamp defensivo: garante total_score no intervalo 0-10."""
        if v is None:
            return v
        v = float(v)
        return max(0.0, min(v, 10.0))
    
    @model_validator(mode='after')
    def calculate_total_if_missing(self):
        """
        Calcula total_score se ausente; detecta automaticamente escala 0-1.
        
        Se todos os criteria_scores individuais forem ≤ 1.0,
        assume-se que o LLM utilizou escala 0-1 (ex: 0.8 em vez de 8.0)
        e multiplica por 10 para normalizar à escala 0-10.
        """
        if not self.criteria_scores:
            if self.total_score is None:
                self.total_score = 0.0
            return self
        
        calculated = sum(cs.score for cs in self.criteria_scores)
        
        # Detecção de escala 0-1: todos os scores individuais ≤ 1.0
        if all(cs.score <= 1.0 for cs in self.criteria_scores):
            logger.warning(
                "Escala 0-1 detectada: %d critérios com scores ≤ 1.0 "
                "(soma=%.4f). Multiplicando por 10 para normalizar à escala 0-10.",
                len(self.criteria_scores),
                calculated,
            )
            calculated = calculated * 10.0
        
        if self.total_score is None:
            self.total_score = min(calculated, 10.0)
        
        return self


class DivergenceAnalysis(BaseModel):
    """
    Análise de divergência entre dois corretores.
    Usada pelo árbitro para decidir se precisa intervir.
    """
    
    corretor_1_score: float = Field(..., ge=0.0)
    corretor_2_score: float = Field(..., ge=0.0)
    absolute_difference: float = Field(..., ge=0.0)
    percentage_difference: float = Field(..., ge=0.0, le=100.0)
    threshold: float = Field(default=2.0, gt=0.0)
    requires_arbitration: bool = Field(
        ...,
        description="True se divergência excede o threshold"
    )
    
    @model_validator(mode='after')
    def calculate_differences(self):
        """Calcula as diferenças automaticamente."""
        self.absolute_difference = abs(
            self.corretor_1_score - self.corretor_2_score
        )
        
        avg_score = (self.corretor_1_score + self.corretor_2_score) / 2.0
        if avg_score > 0:
            self.percentage_difference = (
                self.absolute_difference / avg_score
            ) * 100.0
        else:
            self.percentage_difference = 0.0
        
        self.requires_arbitration = (
            self.absolute_difference > self.threshold
        )
        
        return self
