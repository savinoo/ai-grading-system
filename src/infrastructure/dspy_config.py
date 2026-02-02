import dspy
import os
from src.config.settings import settings

def configure_dspy():
    """
    Configura o backend do DSPy com o modelo LM definido nas settings.
    Suporta OpenAI e Google Gemini.
    """
    model_name = settings.MODEL_NAME.lower()
    
    if "gemini" in model_name:
        # Configuração para Google Gemini
        # Requer: pip install google-generativeai
        try:
            # Importa dinamicamente dspy.Google
            # Remove prefixo 'models/' se existir, pois dspy.Google já lida bem, 
            # mas para LiteLLM/GenerativeAI puro, o ID limpo é preferível na v1beta
            clean_model = model_name.replace("models/", "")
            
            lm = dspy.Google(
                model=clean_model,
                api_key=settings.GOOGLE_API_KEY,
                temperature=settings.TEMPERATURE
            )
        except (AttributeError, NameError):
             # Fallback: dspy-ai versions variam muito nas interfaces de Google.
             # Tenta usar a classe genérica LM do novo dspy
             lm = dspy.LM(f"google/{model_name}", api_key=settings.GOOGLE_API_KEY)

    else:
        # Configuração Padrão (OpenAI)
        try:
            lm = dspy.LM(f"openai/{settings.MODEL_NAME}", api_key=settings.OPENAI_API_KEY)
        except:
            lm = dspy.OpenAI(
                model=settings.MODEL_NAME, 
                api_key=settings.OPENAI_API_KEY,
                temperature=settings.TEMPERATURE
            )
        
    dspy.settings.configure(lm=lm)
