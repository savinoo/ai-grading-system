from typing import Dict, Any

from fastapi import HTTPException

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.users.change_password_service_interface import ChangePasswordServiceInterface

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError

from src.core.logging_config import get_logger

class ChangePasswordController(ControllerInterface):
    """
    Controller para troca de senha de usuário autenticado.
    """

    def __init__(self, service: ChangePasswordServiceInterface) -> None:
        self.__service = service
        self.__logger = get_logger(__name__)

    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Manipula requisição de troca de senha.

        Args:
            http_request: Requisição HTTP com body contendo current_password e new_password,
                        e token_infos com sub (user UUID).

        Returns:
            HttpResponse com confirmação da troca
        """
        db = http_request.db
        token_infos = http_request.token_infos
        body: Dict[str, Any] = http_request.body

        user_uuid = token_infos.get("sub") if token_infos else None
        if not user_uuid:
            return HttpResponse(
                status_code=401,
                body={"error": "Token inválido: sub não encontrado"}
            )

        current_password = body.get("current_password")
        new_password = body.get("new_password")

        if not current_password or not new_password:
            return HttpResponse(
                status_code=400,
                body={"error": "Senha atual e nova senha são obrigatórias"}
            )

        if len(new_password) < 8:
            return HttpResponse(
                status_code=400,
                body={"error": "A nova senha deve ter no mínimo 8 caracteres"}
            )

        if current_password == new_password:
            return HttpResponse(
                status_code=400,
                body={"error": "A nova senha não pode ser igual à senha atual"}
            )

        try:
            result = self.__service.change_password(db, user_uuid, current_password, new_password)
            return HttpResponse(status_code=200, body=result)

        except NotFoundError as e:
            self.__logger.warning("Usuário não encontrado: %s", str(e))
            return HttpResponse(status_code=404, body={"error": str(e)})

        except UnauthorizedError as e:
            self.__logger.warning("Senha atual incorreta: %s", str(e))
            return HttpResponse(status_code=401, body={"error": str(e)})

        except Exception as e:
            self.__logger.error("Erro ao trocar senha: %s", str(e))
            raise HTTPException(status_code=500, detail="Erro interno do servidor") from e
