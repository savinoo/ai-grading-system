from dataclasses import dataclass
from typing import Optional

@dataclass
class CallerMeta:
    """
    Metadados do chamador da API.
    """
    
    ip: str
    user_agent: str
    caller_app: Optional[str]
    caller_user: Optional[str]
