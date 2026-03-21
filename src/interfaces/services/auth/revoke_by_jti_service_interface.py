from __future__ import annotations

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from src.domain.auth.auth import RevokeByJti

class RevokeByJtiServiceInterface(ABC):
    """Revoga um token JWT com base no JTI fornecido.
    
    Attributes:
        __logger (Logging.logger): Logger para registrar operações e erros.
        __repo (ApiVersionControlRepositoryInterface): Repositório para operações de controle de versão da API.
    """
    
    @abstractmethod
    def revoke (self, db: Session, body: RevokeByJti) -> None:
        raise NotImplementedError
