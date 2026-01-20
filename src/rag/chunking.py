# src/rag/chunking.py
import logging
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.infrastructure.vector_db import get_vector_store

logger = logging.getLogger(__name__)

def process_and_index_pdf(file_path: str, discipline: str, topic: str):
    """
    Ingestão de Dados da Matéria (Seção 4.2.1.1 do TCC).
    
    1. Carrega o PDF.
    2. Aplica Chunking Estrutural (Adaptive).
    3. Enriquece com Metadados (Fundamental para EU-C01 e Filtragem).
    4. Indexa no Vector Database.
    """
    logger.info(f"Iniciando ingestão de: {file_path} [{discipline}/{topic}]")
    
    # 1. Carregamento (Loader)
    loader = PyPDFLoader(file_path)
    raw_docs = loader.load()
    
    # 2. Chunking Estrutural (Adaptive Strategy - TCC Seção 2.1)
    # Tenta manter parágrafos e seções juntos.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # Tamanho alvo do chunk
        chunk_overlap=200,    # Sobreposição para manter contexto nas bordas
        separators=["\n\n", "\n", ".", " ", ""] # Prioridade de quebra
    )
    chunks = text_splitter.split_documents(raw_docs)
    
    # 3. Enriquecimento de Metadados (Tagging)
    # Isso viabiliza a "Filtragem de Metadados" (TCC Seção 2.2)
    for doc in chunks:
        doc.metadata["discipline"] = discipline
        doc.metadata["topic"] = topic
        doc.metadata["source"] = file_path
    
    # 4. Indexação
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    
    logger.info(f"Sucesso! {len(chunks)} vetores indexados para '{topic}'.")
    
    return len(chunks)

# Exemplo de uso manual para popular o banco inicialmente
if __name__ == "__main__":
    # Simulação da EU-C01
    process_and_index_pdf(
        file_path="data/raw/apostila_algoritmos.pdf",
        discipline="Computação",
        topic="Estrutura de Dados"
    )