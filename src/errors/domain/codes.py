from enum import StrEnum

class ErrorCode(StrEnum):
    """Enumeração dos códigos de erro de domínio/serviço."""
    
    VALIDATION = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    EXTERNAL = "external_service_error"
    CONFLICT = "conflict"
    UNEXPECTED = "unexpected_error"
    DATA_BASE = "data_base_error"
