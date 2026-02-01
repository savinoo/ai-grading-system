# src/infrastructure/llm_factory.py
import os
from langchain_core.language_models import BaseChatModel
from src.config.settings import settings

def get_chat_model(temperature: float = None, model_name: str = None) -> BaseChatModel:
    """
    Factory para criar instâncias de LLM (ChatOpenAI ou Gemni) 
    baseado na configuração e disponibilidade de chaves.
    """
    if temperature is None:
        temperature = settings.TEMPERATURE
    
    if model_name is None:
        model_name = settings.MODEL_NAME

    # Checa se é um modelo Gemini
    if "gemini" in model_name.lower():
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY não encontrada no .env para usar modelo Gemini.")
            
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=settings.GOOGLE_API_KEY,
            convert_system_message_to_human=True # Gemini as vezes prefere isso
        )
    
    # Fallback para OpenAI
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY
        )
