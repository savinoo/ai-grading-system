from typing import Dict, Any

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.users.reset_password_service_interface import ResetPasswordServiceInterface
from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse
from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError
from src.core.logging_config import get_logger


class ResetPasswordController(ControllerInterface):
    """
    Controller para reset de senha com código de recuperação.
    """
    
    def __init__(self, reset_password_service: ResetPasswordServiceInterface):
        self.__reset_password_service = reset_password_service
        self.__logger = get_logger(__name__)
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Manipula requisição de reset de senha.
        
        Args:
            http_request: Requisição HTTP com body contendo email, code e new_password
            
        Returns:
            HttpResponse com confirmação de reset
            
        Raises:
            NotFoundError: Se usuário não for encontrado
            UnauthorizedError: Se código for inválido
        """
        body: Dict[str, Any] = http_request.body
                
        email = body.get("email")
        code = body.get("code")
        new_password = body.get("new_password")
        
        if not email or not code or not new_password:
            return HttpResponse(
                status_code=400,
                body={"error": "Email, código e nova senha são obrigatórios"}
            )
        
        # Validação básica de senha
        if len(new_password) < 8:
            return HttpResponse(
                status_code=400,
                body={"error": "A senha deve ter no mínimo 8 caracteres"}
            )
        
        try:
            result = self.__reset_password_service.reset_password(
                http_request.db,
                email,
                code,
                new_password
            )
            
            self.__logger.info("Senha resetada com sucesso para: %s", email)
            
            return HttpResponse(
                status_code=200,
                body=result
            )
            
        except NotFoundError as e:
            self.__logger.warning("Usuário não encontrado: %s", email)
            return HttpResponse(
                status_code=404,
                body={"error": str(e)}
            )
            
        except UnauthorizedError as e:
            self.__logger.warning("Código inválido ou expirado: %s", str(e))
            return HttpResponse(
                status_code=401,
                body={"error": str(e)}
            )
