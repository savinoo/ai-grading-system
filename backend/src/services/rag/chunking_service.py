"""
Serviço de Chunking - Processamento de PDFs em chunks estruturados.
Responsável por carregar e dividir documentos PDF em partes menores.
"""

import logging
from typing import List
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class ChunkingService:
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
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ";", " ", ""],
            length_function=len,
            is_separator_regex=False
        )
        
        logger.info(
            "ChunkingService inicializado",
            extra={
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
            }
        )
    
    def process_pdf(self, file_path: str) -> List[Document]:
        """
        Carrega PDF e retorna chunks (sem metadados específicos ainda).
        
        Os metadados de prova/disciplina serão adicionados pelo IndexingService.
        Aqui preservamos apenas metadados do PyPDFLoader (source, page).
        
        Args:
            file_path: Caminho absoluto do PDF no filesystem
            
        Returns:
            Lista de Document (LangChain) com page_number e source
            
        Raises:
            FileNotFoundError: Se o arquivo não existir
            ValueError: Se o arquivo não for PDF válido
            
        Examples:
            >>> chunking = ChunkingService()
            >>> chunks = chunking.process_pdf("/data/uploads/exam_material.pdf")
            >>> len(chunks)
            15
            >>> chunks[0].metadata
            {'source': '/data/uploads/exam_material.pdf', 'page': 0}
        """
        # Validar arquivo existe
        path = Path(file_path)
        if not path.exists():
            logger.error("Arquivo não encontrado: %s", file_path)
            raise FileNotFoundError(f"PDF não encontrado: {file_path}")
        
        if not path.suffix.lower() == '.pdf':
            logger.error("Arquivo não é PDF: %s", file_path)
            raise ValueError(f"Arquivo deve ser PDF: {file_path}")
        
        logger.info("Processando PDF: %s", file_path)
        
        try:
            # Carregar PDF
            loader = PyPDFLoader(file_path)
            raw_docs = loader.load()
            
            if not raw_docs:
                logger.warning("PDF vazio ou não legível: %s", file_path)
                return []
            
            logger.debug(
                "PDF carregado: %d páginas",
                len(raw_docs)
            )
            
            # Dividir em chunks
            chunks = self.text_splitter.split_documents(raw_docs)
            
            logger.info(
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
            logger.error(
                "Erro ao processar PDF: %s - %s",
                file_path,
                str(e),
                exc_info=True
            )
            raise
    
    def process_multiple_pdfs(self, file_paths: List[str]) -> List[Document]:
        """
        Processa múltiplos PDFs em batch.
        
        Args:
            file_paths: Lista de caminhos de PDFs
            
        Returns:
            Lista consolidada de chunks de todos os PDFs
            
        Note:
            Erros em PDFs individuais são logados mas não interrompem o batch.
        """
        all_chunks = []
        
        for file_path in file_paths:
            try:
                chunks = self.process_pdf(file_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(
                    "Falha ao processar PDF %s: %s. Continuando batch...",
                    file_path,
                    str(e)
                )
                continue
        
        logger.info(
            "Batch processing concluído: %d PDFs → %d chunks",
            len(file_paths),
            len(all_chunks)
        )
        
        return all_chunks
    
    def get_chunk_stats(self, chunks: List[Document]) -> dict:
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
