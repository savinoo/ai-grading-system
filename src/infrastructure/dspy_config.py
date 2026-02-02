import dspy
import os
from src.config.settings import settings

def configure_dspy():
    """
    Configura o backend do DSPy com o modelo LM definido nas settings.
    Suporta OpenAI, Google Gemini e outros via LiteLLM.
    """
    model_name = settings.MODEL_NAME.lower()
    
    # Limpeza básica de prefixos legados
    clean_name = model_name.replace("models/", "").replace("google/", "").replace("gemini/", "")
    
    if "gemini" in model_name:
        # Configuração para Gemini via LiteLLM (dspy.LM)
        # Formato esperado: gemini/gemini-2.0-flash
        provider_model = f"gemini/{clean_name}"
        
        # dspy.LM é a interface moderna (v2.5+) que usa LiteLLM por baixo dos panos
        # e suporta async nativo melhor que dspy.Google
        lm = dspy.LM(model=provider_model, api_key=settings.GOOGLE_API_KEY, temperature=settings.TEMPERATURE)

    elif "gpt" in model_name:
        # Configuração OpenAI
        lm = dspy.LM(model=f"openai/{clean_name}", api_key=settings.OPENAI_API_KEY, temperature=settings.TEMPERATURE)
        
    else:
        # Fallback genérico (tenta usar como está ou assume OpenAI)
        try:
            lm = dspy.LM(model=model_name)
        except:
            # Último recurso: dspy.OpenAI legado
            lm = dspy.OpenAI(model=model_name, api_key=settings.OPENAI_API_KEY)
        
    dspy.settings.configure(lm=lm)
