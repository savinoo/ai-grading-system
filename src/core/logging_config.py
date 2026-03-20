import os
import sys
import json
import logging
from typing import Any, Optional
from contextvars import ContextVar, Token

_request_id_ctx: ContextVar[Optional[str]] = ContextVar("_request_id", default=None)

def set_request_id(value: Optional[str]) -> Token:
    return _request_id_ctx.set(value)

def get_request_id() -> Optional[str]:
    return _request_id_ctx.get()

class JsonFormatter(logging.Formatter):
    """
    Classe que formata logs em JSON.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%f%z"),  # com milissegundos
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
            "file": record.pathname,
        }
        
        rid = get_request_id()
        if rid:
            payload["request_id"] = rid
        
        # Adicionar campos extras customizados
        if hasattr(record, "extra"):
            payload.update(record.extra)
            
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
            
        return json.dumps(payload, ensure_ascii=False)

def _build_handler(stream: Any, level: int, json_mode: bool) -> logging.Handler:
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    if json_mode:
        handler.setFormatter(JsonFormatter())
    else:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
    return handler

def setup_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    json_mode = os.getenv("LOG_JSON", "false").lower() in ("1", "true", "yes")

    root = logging.getLogger()
    root.setLevel(log_level)

    for h in list(root.handlers):
        root.removeHandler(h)

    stdout_handler = _build_handler(sys.stdout, logging.DEBUG, json_mode)
    stdout_handler.addFilter(lambda r: r.levelno < logging.ERROR)

    stderr_handler = _build_handler(sys.stderr, logging.ERROR, json_mode)

    root.addHandler(stdout_handler)
    root.addHandler(stderr_handler)

    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    logging.getLogger("gunicorn").setLevel(log_level)
    logging.getLogger("gunicorn.error").setLevel(logging.ERROR)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
