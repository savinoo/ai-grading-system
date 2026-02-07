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
    
    # === OPENAI ===
    OPENAI_API_KEY: str = Field(..., description="Chave da API OpenAI")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="Modelo padrão")
    OPENAI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    
    # === CHROMADB ===
    CHROMA_PERSIST_DIRECTORY: str = Field(default="./chroma_db", description="Diretório do ChromaDB")
    CHROMA_COLLECTION_NAME: str = Field(default="documents", description="Nome da coleção")
    
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
