from __future__ import annotations

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from src.domain.requests.auth.login import UserLoginRequest
from src.domain.responses.auth.login import UserLoginResponse

from src.domain.http.caller_domains import CallerMeta

class UserLoginServiceInterface(ABC):
    """
    Interface do serviço para autenticação de usuários e emissão de tokens JWT.
    """

    @abstractmethod
    def login(self, db: Session, user_request: UserLoginRequest, caller_meta: CallerMeta) -> UserLoginResponse:
        """
        Autentica um usuário usando email e senha, e retorna tokens JWT.

        Args:
            db: Sessão do banco de dados
            user_request: Objeto de requisição contendo email e senha
            caller_meta: Metadados do chamador (IP, app, user)

        Returns:
            UserLoginResponse: Resposta contendo tokens e dados do usuário

        Raises:
            NotFoundError: Se o usuário não for encontrado
            UnauthorizedError: Se a senha estiver incorreta ou usuário inativo
            SqlError: Se ocorrer um erro ao acessar o banco de dados
        """
        raise NotImplementedError()
