from __future__ import annotations

from typing import List
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.interfaces.services.rag.chunking_service_interface import ChunkingServiceInterface

from src.errors.domain.validate_error import ValidateError

from src.core.logging_config import get_logger

class ChunkingService(ChunkingServiceInterface):
    """
    Processa PDFs em chunks estruturados para indexação vetorial.
    
    Usa RecursiveCharacterTextSplitter para manter coerência semântica,
    priorizando quebras em parágrafos e sentenças.
    """
    
    def __init__(self, chunk_size: int = 4000, chunk_overlap: int = 200):
        """
        Inicializa o serviço de chunking.
        
        Args:
            chunk_size: Tamanho máximo do chunk em caracteres (padrão: 4000)
            chunk_overlap: Overlap entre chunks para manter contexto (padrão: 200)
        """
        self.__logger = get_logger(__name__)
        
        self.__text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ";", " ", ""],
            length_function=len,
            is_separator_regex=False
        )
        
        self.__logger.info(
            "ChunkingService inicializado",
            extra={
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
            }
        )
    
    async def process_pdf(self, file_path: str) -> List[Document]:
        """
        Carrega PDF e retorna chunks (sem metadados específicos ainda).
        
        Os metadados de prova/disciplina serão adicionados pelo IndexingService.
        Aqui preservamos apenas metadados do PyPDFLoader (source, page).
        
        Args:
            file_path: Caminho absoluto do PDF no filesystem
            
        Returns:
            Lista de Document (LangChain) com page_number e source
            
        Raises:
            ValidateError: Se o arquivo não existir ou não for PDF válido
            
        Examples:
            >>> chunking = ChunkingService()
            >>> chunks = await chunking.process_pdf("/data/uploads/exam_material.pdf")
            >>> len(chunks)
            15
            >>> chunks[0].metadata
            {'source': '/data/uploads/exam_material.pdf', 'page': 0}
        """
        # Validar arquivo existe
        path = Path(file_path)
        if not path.exists():
            self.__logger.error("Arquivo não encontrado: %s", file_path)
            raise ValidateError(
                message="PDF não encontrado",
                context={"file_path": file_path}
            )
        
        if not path.suffix.lower() == '.pdf':
            self.__logger.error("Arquivo não é PDF: %s", file_path)
            raise ValidateError(
                message="Arquivo deve ser PDF",
                context={"file_path": file_path, "extension": path.suffix}
            )
        
        self.__logger.info("Processando PDF: %s", file_path)
        
        try:
            # Carregar PDF
            loader = PyPDFLoader(file_path)
            raw_docs = loader.load()
            
            if not raw_docs:
                self.__logger.warning("PDF vazio ou não legível: %s", file_path)
                return []
            
            self.__logger.debug(
                "PDF carregado: %d páginas",
                len(raw_docs)
            )
            
            # Dividir em chunks
            chunks = self.__text_splitter.split_documents(raw_docs)
            
            self.__logger.info(
                "PDF dividido em chunks",
                extra={
                    "file": file_path,
                    "pages": len(raw_docs),
                    "chunks": len(chunks),
                    "avg_chunk_size": sum(len(c.page_content) for c in chunks) // len(chunks) if chunks else 0
                }
            )
            
            return chunks
            
        except Exception as e:
            self.__logger.error(
                "Erro ao processar PDF: %s - %s",
                file_path,
                str(e),
                exc_info=True
            )
            raise
    
    def _get_chunk_stats(self, chunks: List[Document]) -> dict:
        """
        Retorna estatísticas sobre os chunks gerados.
        Útil para debugging e otimização.
        
        Args:
            chunks: Lista de chunks
            
        Returns:
            Dict com estatísticas (count, avg_size, min_size, max_size)
        """
        if not chunks:
            return {
                "count": 0,
                "avg_size": 0,
                "min_size": 0,
                "max_size": 0
            }
        
        sizes = [len(chunk.page_content) for chunk in chunks]
        
        return {
            "count": len(chunks),
            "avg_size": sum(sizes) // len(sizes),
            "min_size": min(sizes),
            "max_size": max(sizes),
            "total_chars": sum(sizes)
        }
