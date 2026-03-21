from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from langchain_core.documents import Document

class ChunkingServiceInterface(ABC):
    """
    Interface para o serviço de processamento de PDFs em chunks.
    """
    
    @abstractmethod    
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
        raise NotImplementedError()
