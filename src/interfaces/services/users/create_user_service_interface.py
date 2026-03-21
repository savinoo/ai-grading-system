from __future__ import annotations

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from src.domain.requests.users.user_create_request import UserCreateRequest
from src.domain.responses.users.user_response import UserResponse

class CreateUserServiceInterface(ABC):
    """
    Serviço para criação de usuários.
    
    Centraliza a lógica de negócio relacionada a criação usuários,
    incluindo criação e formatação de respostas.
    """
    
    @abstractmethod
    async def create_user(self, db: Session, request: UserCreateRequest) -> UserResponse:
        """
        Cria um novo usuário.
        
        Args:
            db: Sessão do banco de dados
            request: Dados do usuário a ser criado
            
        Returns:
            UserResponse: Dados do usuário criado
            
        Raises:
            AlreadyExistingError: Se o email já estiver cadastrado
            SqlError: Para erros de banco de dados
        """
        raise NotImplementedError()
