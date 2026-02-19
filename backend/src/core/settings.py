from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Classe responsável por armazenar as configurações do sistema."""
    
    # === AMBIENTE ===
    ENV: str = Field(default="dev", description="Ambiente de execução")
    
    # === LOGS ===
    LOG_LEVEL: str = Field(default="INFO", description="Nível de log")
    LOG_JSON: bool = Field(default=False, description="Logs em formato JSON")
    
    # === CORS ===
    ALLOW_ORIGINS: list[str] = [
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:8000"
    ]
    ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CSP_REPORT_ONLY: bool = False
    
    # === DATABASE (POSTGRES) ===
    DATABASE_URL: str = Field(..., description="Connection string do PostgreSQL")
    
    # === RAG & Vector Database ===
    CHROMA_PERSIST_DIRECTORY: str = Field(default="./data/chromadb", description="Diretório de persistência do ChromaDB")
    EMBEDDING_MODEL: str = Field(default="models/gemini-embedding-001", description="Modelo de embeddings")
    EMBEDDING_PROVIDER: str = Field(default="google", description="Provedor de embeddings (google, openai)")
    
    # === LLM Configuration ===
    LLM_PROVIDER: str = Field(default="gemini", description="Provedor de LLM (openai, gemini, litellm)")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="Chave da API OpenAI")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Chave da API Google")
    LLM_MODEL_NAME: str = Field(default="gemini-2.0-flash-exp", description="Nome do modelo LLM")
    LLM_TEMPERATURE: float = Field(default=0.0, ge=0.0, le=2.0, description="Temperatura do LLM (0=determinístico)")
    LLM_MAX_RETRIES: int = Field(default=3, ge=1, le=10, description="Máximo de tentativas em caso de falha")
    
    # === DSPy ===
    DSPY_CACHE_DIR: str = Field(default="./data/dspy_cache", description="Diretório de cache do DSPy")
    
    # === LangSmith (Observability) ===
    LANGSMITH_API_KEY: Optional[str] = Field(default=None, description="Chave da API LangSmith")
    LANGSMITH_ENDPOINT: str = Field(default="https://api.smith.langchain.com", description="Endpoint da API LangSmith")
    LANGSMITH_PROJECT_NAME: str = Field(default="ai-grading-backend", description="Nome do projeto no LangSmith")
    LANGSMITH_TRACING_ENABLED: bool = Field(default=False, description="Habilitar rastreamento no LangSmith")
    
    # === Grading Workflow ===
    DIVERGENCE_THRESHOLD: float = Field(default=2.0, ge=0.0, description="Limiar de divergência entre avaliadores")
    RAG_TOP_K: int = Field(default=4, ge=1, le=20, description="Número de documentos recuperados pelo RAG")

    # === Concorrência de API ===
    API_CONCURRENCY: int = Field(default=10, ge=1, description="Máximo de chamadas simultâneas à API do LLM")
    API_THROTTLE_SLEEP: float = Field(default=0.2, ge=0.0, description="Segundos de espera entre chamadas dentro do semáforo")
    
    # === BCRYPT ===
    BCRYPT_ROUNDS: int = Field(default=12, ge=4, le=31, description="Número de rounds para bcrypt")
    
    # === JWT ===
    SECRET_KEY: str = Field(..., description="Chave secreta para assinatura de tokens JWT")
    JWT_ALGORITHM: str = Field(default="HS256", description="Algoritmo JWT")
    JWT_ACCESS_TOKEN_TTL: int = Field(default=900, description="TTL do access token em segundos (15 min)")
    JWT_REFRESH_TOKEN_TTL: int = Field(default=604800, description="TTL do refresh token em segundos (7 dias)")
    MAX_ACTIVE_SESSIONS: int = Field(default=4, description="Número máximo de sessões ativas por usuário")
    
    # === TIMEZONE ===
    TIME_ZONE: str = Field(default="America/Sao_Paulo", description="Timezone da aplicação")
    
    # === BREVO (EMAIL) ===
    BREVO_API_KEY: str = Field(..., description="Chave da API Brevo")
    BREVO_VERIFICATION_TEMPLATE_ID: int = Field(..., description="ID do template de verificação de email")
    BREVO_RECOVERY_CODE_TEMPLATE_ID: int = Field(..., description="ID do template de código de recuperação")
    
    # === RECOVERY CODE ===
    RECOVERY_CODE_LENGTH: int = Field(default=6, description="Tamanho do código de recuperação")
    RECOVERY_CODE_EXPIRY_MINUTES: int = Field(default=15, description="Minutos até expiração do código")
    RECOVERY_CODE_MAX_ATTEMPTS: int = Field(default=3, description="Máximo de tentativas de validação")
    
    # === FILE UPLOAD ===
    UPLOAD_DIR: str = Field(default="./data/uploads", description="Diretório raiz para uploads")
    MAX_FILE_SIZE_MB: int = Field(default=200, description="Tamanho máximo de arquivo em MB")
    ALLOWED_MIME_TYPES: list[str] = Field(
        default=["application/pdf"],
        description="Tipos MIME permitidos para upload"
    )
    
    @field_validator("ALLOW_ORIGINS")
    @classmethod
    def validate_cors_in_production(cls, v: list[str], info) -> list[str]:
        """Previne CORS aberto em produção."""
        if info.data.get("ENV") == "prd" and "*" in v:
            raise ValueError("CORS wildcard não permitido em produção")
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignora variáveis extras do .env
    )

settings = Settings()
