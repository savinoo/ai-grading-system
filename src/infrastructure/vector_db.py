# src/infrastructure/vector_db.py
import os
import logging
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from src.config.settings import settings

logger = logging.getLogger(__name__)

def get_vector_store() -> Chroma:
    """
    Inicializa e retorna a conexão com o ChromaDB (Persistente).
    
    Técnica: Usamos OpenAIEmbeddings para alinhar a qualidade vetorial 
    com o modelo de raciocínio (GPT-4o), garantindo alta fidelidade semântica.
    """
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small" # Eficiente e barato
    )
    
    # Ensure absolute path for persistence
    base_dir = os.getcwd()
    persist_directory = os.path.join(base_dir, "data", "vector_store")
    
    vector_store = Chroma(
        collection_name="material_didatico_tcc",
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )
    
    return vector_store