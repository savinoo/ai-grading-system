from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session


class ChangePasswordServiceInterface(ABC):
    """
    Interface para serviço de troca de senha autenticada.
    """

    @abstractmethod
    def change_password(
        self,
        db: Session,
        user_uuid: str,
        current_password: str,
        new_password: str,
    ) -> Dict[str, Any]:
        """
        Troca a senha do usuário autenticado.

        Args:
            db: Sessão do banco de dados
            user_uuid: UUID do usuário extraído do token JWT
            current_password: Senha atual em texto puro
            new_password: Nova senha em texto puro

        Returns:
            Dict com confirmação da troca

        Raises:
            NotFoundError: Se o usuário não for encontrado
            UnauthorizedError: Se a senha atual estiver errada
        """
        raise NotImplementedError()
