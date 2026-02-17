
# FastAPI imports
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

# Middlewares
from src.main.middlewares.request_id import RequestIdMiddleware
from src.main.middlewares.request_logging import RequestLoggingMiddleware
from src.main.middlewares.security_headers import SecurityHeadersMiddleware

# Core
from src.core.settings import settings
from src.core.logging_config import setup_logging, get_logger
from src.core.dspy_config import configure_dspy

# Rotas
from src.main.routes.auth_routes import router as auth_router
from src.main.routes.users_routes import router as users_router
from src.main.routes.classes_routes import router as classes_router
from src.main.routes.exams_routes import router as exams_router
from src.main.routes.attachments_routes import router as attachments_router
from src.main.routes.grading_criteria_routes import router as grading_criteria_router
from src.main.routes.exam_criteria_routes import router as exam_criteria_router
from src.main.routes.exam_questions_routes import router as exam_questions_router
from src.main.routes.exam_question_criteria_override_routes import router as question_criteria_override_router
from src.main.routes.student_answers_routes import router as student_answers_router
from src.main.routes.results_routes import router as results_router
from src.main.routes.reviews_routes import router as reviews_router
from src.main.routes.dashboard_routes import router as dashboard_router

# Configura o logging conforme as configurações
setup_logging()
logger = get_logger(__name__)


app = FastAPI(
    title="CorretumAI API",
    version="1.0.0",
    debug=(settings.ENV != "prd")
)


# ===== EVENTOS DE STARTUP =====
@app.on_event("startup")
async def startup_event():
    """
    Inicialização de recursos ao iniciar a aplicação.
    """
    logger.info("Iniciando aplicação CorretumAI")
    
    # Configurar DSPy globalmente
    try:
        configure_dspy()
        logger.info("DSPy configurado no startup")
    except Exception as e:
        logger.warning("Falha ao configurar DSPy (não crítico): %s", e)
    
    logger.info("Aplicação inicializada com sucesso")


# ===== MIDDLEWARES =====
# Middleware de Id de Requisição
app.add_middleware(RequestIdMiddleware)

# Middleware para confiar em proxies reversos
@app.middleware("http")
async def force_https_scheme(request: Request, call_next):
    if request.headers.get("x-forwarded-proto") == "https":
        request.scope["scheme"] = "https"
    response = await call_next(request)
    return response

# Middleware de segurança de cabeçalhos
app.add_middleware(
    SecurityHeadersMiddleware,
    csp_report_only=settings.CSP_REPORT_ONLY
)

# Middleware de logging de requisições
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=["*"],
)

# Middleware de logging de requisições
app.add_middleware(RequestLoggingMiddleware)

# Manipulador de erros de validação
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Captura e loga erros de validação do Pydantic (status 422).
    """
    errors = exc.errors()

    # Remove objetos não serializáveis do ctx
    for error in errors:
        if "ctx" in error and "error" in error["ctx"]:
            error["ctx"]["error"] = str(error["ctx"]["error"])

    logger.error(
        "Erro de validação (422) na requisição: %s %s - Detalhes: %s",
        request.method,
        request.url.path,
        errors
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
            "body": exc.body
        }
    )

# Rota raiz redireciona para health check
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="health")

# Rota de health check
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Rota para verificar a saúde da aplicação.
    """
    logger.info("Health check chamado", extra={"component": "health"})
    return {"status": "ok"}

# ===== OUTRAS ROTAS =====
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(classes_router)
app.include_router(exams_router)
app.include_router(exam_questions_router)
app.include_router(question_criteria_override_router)
app.include_router(student_answers_router)
app.include_router(attachments_router)
app.include_router(grading_criteria_router)
app.include_router(exam_criteria_router)
app.include_router(results_router)
app.include_router(reviews_router)
app.include_router(dashboard_router)
