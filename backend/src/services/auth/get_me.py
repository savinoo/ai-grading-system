from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface
from src.interfaces.services.auth.get_me_interface import GetMeServiceInterface

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.sql_error import SqlError

from src.core.logging_config import get_logger

class GetMeService(GetMeServiceInterface):
    """
    Serviço para obter informações do usuário logado.
    
    Attributes:
        __repo: Repositório de usuários para operações no banco de dados.
        __logger: Logger para registrar eventos e erros.
    """
    
    def __init__(self, repo: UserRepositoryInterface) -> None:
        self.__repo = repo
        self.__logger = get_logger(__name__)
    
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
        self.__logger.debug("Obtendo informações do usuário: %s", user_uuid)
        
        try:
            user = self.__repo.get_by_uuid(db, user_uuid)
            
            if not user:
                self.__logger.error("Usuário não encontrado: %s", user_uuid)
                raise NotFoundError(f"Usuário {user_uuid} não encontrado.")
            
            return self.__format_response(user)
            
        except NoResultFound as nfe:
            self.__logger.error("Usuário não encontrado: %s", user_uuid)
            raise NotFoundError(f"Usuário {user_uuid} não encontrado.") from nfe
        except Exception as e:
            self.__logger.error(
                "Erro ao obter informações do usuário %s: %s",
                user_uuid,
                str(e)
            )
            raise SqlError("Erro ao acessar o banco de dados.") from e
    
    def __format_response(self, user) -> dict:
        """Formata a resposta com as informações do usuário."""
        return {
            "id": user.id,
            "uuid": str(user.uuid),
            "email": user.email,
            "user_type": user.user_type,
            "active": user.active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
