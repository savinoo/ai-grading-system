from typing import Generator
from sqlalchemy.orm import Session

from src.models.settings.postgres_conn_handler import get_db_session


def get_db() -> Generator[Session, None, None]:
    """
    Dependência do FastAPI para injeção de sessão do banco de dados.
    
    Yields:
        Session: Sessão do banco de dados com gerenciamento automático
        
    Example:
        ```python
        @app.get("/items")
        async def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
        ```
        
    Note:
        Usa get_db_session() que já implementa:
        - Commit automático em caso de sucesso
        - Rollback automático em exceções
        - Logging de erros
        - Fechamento garantido da sessão
    """
    with get_db_session() as session:
        yield session
