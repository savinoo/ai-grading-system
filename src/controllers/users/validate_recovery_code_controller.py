from typing import Dict, Any

from src.interfaces.controllers.controllers_interface import ControllerInterface
from src.interfaces.services.users.validate_recovery_code_service_interface import ValidateRecoveryCodeServiceInterface

from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

from src.errors.domain.not_found import NotFoundError
from src.errors.domain.unauthorized import UnauthorizedError

from src.core.logging_config import get_logger


class ValidateRecoveryCodeController(ControllerInterface):
    """
    Controller para validação de código de recuperação.
    """
    
    def __init__(self, validate_recovery_code_service: ValidateRecoveryCodeServiceInterface):
        self.__validate_recovery_code_service = validate_recovery_code_service
        self.__logger = get_logger(__name__)
    
    def handle(self, http_request: HttpRequest) -> HttpResponse:
        """
        Manipula requisição de validação de código.
        
        Args:
            http_request: Requisição HTTP com body contendo email e code
            
        Returns:
            HttpResponse com resultado da validação
            
        Raises:
            NotFoundError: Se usuário não for encontrado
            UnauthorizedError: Se código for inválido
        """
        body: Dict[str, Any] = http_request.body
        
        db = http_request.db
        email = body.get("email")
        code = body.get("code")
        
        if not email or not code:
            return HttpResponse(
                status_code=400,
                body={"error": "Email e código são obrigatórios"}
            )
        
        try:
            result = self.__validate_recovery_code_service.validate(db, email, code)
            
            self.__logger.info("Código validado com sucesso para: %s", email)
            
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
