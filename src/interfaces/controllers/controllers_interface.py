from abc import ABC, abstractmethod
from src.domain.http.http_request import HttpRequest
from src.domain.http.http_response import HttpResponse

class ControllerInterface (ABC):
    """
    Classe interface para todas as classe do tipo controller.
    """
    
    @abstractmethod
    def handle (self, http_request: HttpRequest) -> HttpResponse:
        pass
