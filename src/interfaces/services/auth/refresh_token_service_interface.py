from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session

class RefreshTokenServiceInterface(ABC):
    """
    Serviço responsável por renovar tokens de acesso usando refresh tokens.
    """
    
    @abstractmethod
    def refresh(self, db: Session, token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """
        Renova um token de acesso usando um refresh token válido.
        
        Args:
            db (Session): Sessão do banco de dados.
            token_claims (Dict[str, Any]): Claims do refresh token já decodificado.
            
        Returns:
            Dict[str, Any]: Novo token de acesso.
            
        Raises:
            UnauthorizedError: Se o refresh token for inválido ou revogado.
            NotFoundError: Se o refresh token não for encontrado no banco de dados.
            SqlError: Se ocorrer um erro ao acessar o banco de dados.
        """
        raise NotImplementedError()
