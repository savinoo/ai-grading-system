"""
Schemas específicos para RAG (Retrieval-Augmented Generation).
Define estruturas para busca e recuperação de contexto via ChromaDB.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


class RetrievedContext(BaseModel):
    """
    Chunk de documento recuperado via RAG.
    Contém o conteúdo, metadados da fonte e score de relevância.
    """
    
    content: str = Field(
        ...,
        description="Conteúdo textual do chunk recuperado",
        min_length=1
    )
    source_document: str = Field(
        ...,
        description="Nome do documento fonte (ex: prova_2023_ed.pdf)",
        min_length=1
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Número da página no documento original",
        ge=1
    )
    relevance_score: float = Field(
        ...,
        description="Score de similaridade do vector DB (0.0 a 1.0)",
        ge=0.0,
        le=1.0
    )
    
    # Metadados para tracking e filtragem
    discipline: str = Field(
        ...,
        description="Disciplina do material (ex: Estrutura de Dados)",
        min_length=1
    )
    topic: str = Field(
        ...,
        description="Tópico específico (ex: Árvores Binárias)",
        min_length=1
    )
    
    # Metadados adicionais opcionais
    chunk_index: Optional[int] = Field(
        default=None,
        description="Índice do chunk no documento (para ordenação)",
        ge=0
    )


class RAGQueryRequest(BaseModel):
    """
    Request para busca RAG no vector store.
    Define parâmetros de filtragem e recuperação.
    """
    
    query: str = Field(
        ...,
        description="Texto da query para busca semântica",
        min_length=3
    )
    discipline: str = Field(
        ...,
        description="Filtro obrigatório por disciplina",
        min_length=1
    )
    topic: Optional[str] = Field(
        default=None,
        description="Filtro opcional por tópico específico"
    )
    top_k: int = Field(
        default=4,
        description="Número de documentos a recuperar",
        ge=1,
        le=20
    )
    min_relevance_score: float = Field(
        default=0.0,
        description="Score mínimo de relevância para incluir resultado",
        ge=0.0,
        le=1.0
    )
    
    @field_validator('query')
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Garante que a query não é apenas espaços."""
        if not v.strip():
            raise ValueError("Query não pode ser vazia ou apenas espaços")
        return v.strip()


class RAGQueryResponse(BaseModel):
    """
    Response de uma busca RAG.
    Contém os chunks recuperados e metadados da busca.
    """
    
    contexts: List[RetrievedContext] = Field(
        ...,
        description="Lista de contextos recuperados, ordenados por relevância"
    )
    total_found: int = Field(
        ...,
        description="Total de resultados encontrados antes do top_k",
        ge=0
    )
    query: str = Field(
        ...,
        description="Query original que gerou estes resultados"
    )
    
    # Metadados da busca
    avg_relevance_score: Optional[float] = Field(
        default=None,
        description="Score médio de relevância dos resultados",
        ge=0.0,
        le=1.0
    )
    
    @field_validator('contexts')
    @classmethod
    def sort_by_relevance(cls, v: List[RetrievedContext]) -> List[RetrievedContext]:
        """Garante que contextos estão ordenados por relevância (descendente)."""
        return sorted(v, key=lambda x: x.relevance_score, reverse=True)


class DocumentMetadata(BaseModel):
    """
    Metadados de um documento indexado no vector store.
    Usado durante a ingestão de materiais de referência.
    """
    
    filename: str = Field(
        ...,
        description="Nome do arquivo original",
        min_length=1
    )
    discipline: str = Field(
        ...,
        description="Disciplina do material",
        min_length=1
    )
    topic: str = Field(
        ...,
        description="Tópico coberto",
        min_length=1
    )
    document_type: str = Field(
        default="reference_material",
        description="Tipo de documento (reference_material, exam, solution)"
    )
    upload_date: Optional[str] = Field(
        default=None,
        description="Data de upload (ISO format)"
    )
    
    # Metadados opcionais
    semester: Optional[str] = None
    professor_id: Optional[str] = None
    total_pages: Optional[int] = Field(default=None, ge=1)
    
    @field_validator('document_type')
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        """Valida tipos de documento aceitos."""
        allowed = {
            'reference_material',
            'exam',
            'solution',
            'lecture_notes',
            'textbook'
        }
        if v not in allowed:
            raise ValueError(f"document_type deve ser um de: {allowed}")
        return v


class ChunkingConfig(BaseModel):
    """
    Configuração para estratégia de chunking de documentos.
    Define como PDFs serão quebrados em chunks para embedding.
    """
    
    chunk_size: int = Field(
        default=1000,
        description="Tamanho máximo do chunk em caracteres",
        ge=100,
        le=4000
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap entre chunks consecutivos",
        ge=0
    )
    separator: str = Field(
        default="\n\n",
        description="Separador de chunks (newlines, períodos, etc)"
    )
    
    @model_validator(mode='after')
    def validate_overlap_less_than_size(self):
        """Garante que overlap é menor que chunk_size."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap deve ser menor que chunk_size")
        return self
