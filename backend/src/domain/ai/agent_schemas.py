"""
Schemas específicos para agentes corretores (DSPy Signatures).
Define estruturas de saída dos agentes e tipos de correção.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


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
    
    criterion_name: str = Field(
        ...,
        description="Nome do critério avaliado",
        min_length=1
    )
    score: float = Field(
        ...,
        description="Pontuação obtida neste critério",
        ge=0.0
    )
    max_score: float = Field(
        ...,
        description="Pontuação máxima possível neste critério",
        gt=0.0
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Feedback específico sobre este critério"
    )
    
    @field_validator('score')
    @classmethod
    def validate_score_not_exceeds_max(cls, v: float) -> float:
        """Valida que score não excede max_score."""
        # Validação adicional ocorre no model_validator
        if v < 0:
            return 0.0
        return v
    
    @model_validator(mode='after')
    def check_score_range(self):
        """Garante que score não exceda max_score."""
        if self.score > self.max_score:
            self.score = self.max_score
        return self


class AgentCorrection(BaseModel):
    """
    Saída estruturada de um agente corretor (DSPy output).
    
    Força o modelo a gerar raciocínio Chain-of-Thought ANTES da nota,
    garantindo avaliações mais consistentes e explicáveis.
    """
    
    agent_id: AgentID = Field(
        ...,
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
        ...,
        description="Lista de scores por critério avaliado",
        min_length=1
    )
    
    total_score: float = Field(
        ...,
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
    
    @model_validator(mode='after')
    def recalculate_total_score(self):
        """
        Recalcula total_score baseado em criteria_scores.
        Previne erros de cálculo do LLM.
        """
        if self.criteria_scores:
            calculated_total = sum(cs.score for cs in self.criteria_scores)
            
            # Se o LLM forneceu um total muito diferente, corrigir
            if abs(calculated_total - self.total_score) > 0.5:
                self.total_score = calculated_total
        
        return self
    
    @field_validator('total_score')
    @classmethod
    def check_score_range(cls, v: float) -> float:
        """
        Validação defensiva: corrige alucinações de escala.
        Ex: LLM confunde 18/20 com 18/10 → normaliza para 10.0
        """
        if v < 0.0:
            return 0.0
        if v > 100.0:  # Alucinação comum: 90/100 em vez de 9/10
            return min(v / 10.0, 10.0)
        if v > 20.0:  # Pode estar usando escala 0-20
            return min(v / 2.0, 10.0)
        return v


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
