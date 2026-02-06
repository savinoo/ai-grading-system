# pylint: disable=invalid-name

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.core.settings import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexões antes de usar
    pool_size=10,  # Número de conexões mantidas no pool
    max_overflow=20,  # Conexões adicionais permitidas além do pool_size
    pool_recycle=3600,  # Recicla conexões após 1 hora
    pool_timeout=30,  # Timeout ao aguardar conexão disponível
    echo=False,  # Desabilitar logging SQL em produção
    future=True,  # Usar SQLAlchemy 2.0 style
    connect_args={
        "application_name": "AvaliaAI",  # Identificação da aplicação
        "connect_timeout": 10,  # Timeout de conexão em segundos
        "options": "-c statement_timeout=30000",  # Timeout de statement (30s)
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager para gerenciamento automático de sessões.
    
    Yields:
        Session: Sessão de banco de dados
        
    Example:
        ```python
        with get_db_session() as session:
            result = session.query(Model).all()
        ```
        
    Raises:
        Exception: Propaga exceções após rollback
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error("Erro na sessão do banco de dados: %s", str(e))
        session.rollback()
        raise
    finally:
        session.close()


def close_db_connections() -> None:
    """
    Fecha todas as conexões do pool.
    
    Útil para shutdown gracioso da aplicação.
    """
    try:
        engine.dispose()
        logger.info("Conexões do banco de dados fechadas com sucesso")
    except Exception as e:
        logger.error("Erro ao fechar conexões do banco de dados: %s", str(e))
