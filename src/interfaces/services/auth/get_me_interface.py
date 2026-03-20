from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

class GetMeServiceInterface(ABC):
    """
    Serviço para obter informações do usuário logado.
    
    Attributes:
        __repo: Repositório de usuários para operações no banco de dados.
        __logger: Logger para registrar eventos e erros.
    """
    
    @abstractmethod
    def execute(self, db: Session, user_uuid: str) -> dict:
        """
        Obtém as informações do usuário logado.
        
        Args:
            db (Session): Sessão do banco de dados.
            user_uuid (str): UUID do usuário extraído do token.
        
        Returns:
            dict: Informações do usuário.
        
        Raises:
            NotFoundError: Se o usuário não for encontrado.
            SqlError: Se ocorrer erro no banco de dados.
        """
        raise NotImplementedError()
    
