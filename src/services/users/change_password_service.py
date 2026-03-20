from typing import Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.interfaces.services.users.change_password_service_interface import ChangePasswordServiceInterface
from src.interfaces.repositories.user_repository_interface import UserRepositoryInterface

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError

from src.core.security.hash_password import HashPasswordHandler
from src.core.logging_config import get_logger


class ChangePasswordService(ChangePasswordServiceInterface):
    """
    Serviço para troca de senha de usuário autenticado.

    Valida a senha atual antes de atualizar para a nova.
    """

    def __init__(self, user_repository: UserRepositoryInterface) -> None:
        self.__user_repository = user_repository
        self.__hash_handler = HashPasswordHandler()
        self.__logger = get_logger(__name__)

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
        self.__logger.info("Trocando senha do usuário: %s", user_uuid)

        try:
            user = self.__user_repository.get_by_uuid(db, user_uuid)
        except NoResultFound as e:
            self.__logger.warning("Usuário não encontrado: %s", user_uuid)
            raise NotFoundError("Usuário não encontrado") from e

        # Verifica senha atual
        is_valid = self.__hash_handler.verify_password(current_password, user.password_hash)
        if not is_valid:
            self.__logger.warning("Senha atual incorreta para o usuário: %s", user_uuid)
            raise UnauthorizedError("Senha atual incorreta")

        # Gera hash da nova senha e atualiza
        new_hash = self.__hash_handler.generate_password_hash(new_password)
        self.__user_repository.update_password(db, user.id, new_hash)

        self.__logger.info("Senha alterada com sucesso para o usuário: %s", user_uuid)
        return {"message": "Senha alterada com sucesso"}
