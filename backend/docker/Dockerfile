# === STAGE 1: Builder ===
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# === STAGE 2: Runtime ===
FROM python:3.12-slim

WORKDIR /app

# Instalar apenas runtime do PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar virtualenv do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

# Copiar código
COPY --chown=appuser:appuser . .

# Mudar para usuário não-root
USER appuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Labels
LABEL maintainer="lulosavino@gmail.com, maycon.fernandes9@gmail.com" \
    version="1.0" \
    description="CorretumAI Backend API"

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
    "src.main.server.server:app", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--timeout", "240", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]


# Instruções para build e run:
# docker build -t backend_api_corretum_ai -f docker/Dockerfile . 
# docker run -d -p 8000:8000 --name backend_api_corretum_ai_container backend_api_corretum_ai