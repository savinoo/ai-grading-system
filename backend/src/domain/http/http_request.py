from typing import Dict, Optional
from sqlalchemy.orm import Session
from src.domain.http.caller_domains import CallerMeta

class HttpRequest:
    """
    Classe que define com deve ser um request de http
    """
    def __init__(
        self,
        body: Dict = None,
        param: Dict = None,
        headers: Dict = None,
        caller: Optional[CallerMeta] = None,
        token_infos: Dict = None,
        db: Session = None
        ) -> None:
        
        self.body = body
        self.param = param
        self.headers = headers
        self.token_infos = token_infos
        self.db = db
        self.caller = caller
        
