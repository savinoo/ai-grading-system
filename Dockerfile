# ============================================================
# AI Grading System - Dockerfile
# Multi-stage build for Streamlit application
# ============================================================
#
# Recommended .dockerignore entries (see .dockerignore file):
#   __pycache__/  *.pyc  .git/  .github/  .env
#   .streamlit/secrets.toml  data/  notebooks/  tests/
#   *.md  .venv/  venv/  .mypy_cache/  .pytest_cache/
#
# Build:  docker build -t ai-grading-system .
# Run:    docker run -p 8501:8501 --env-file .env ai-grading-system
# ============================================================

# ------------------ Stage 1: Builder -----------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies required by some packages (e.g., numpy, scipy)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies into a prefix we can copy later
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ------------------ Stage 2: Runtime ----------------------
FROM python:3.12-slim AS runtime

# Install only runtime system dependencies (curl for healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source code
COPY app/ ./app/
COPY src/ ./src/
COPY .streamlit/ ./.streamlit/

# Create data directory for ChromaDB persistence (owned by appuser)
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# Set ownership of the application directory
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment configuration
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true

# Expose Streamlit default port
EXPOSE 8501

# Health check against Streamlit internal health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.fileWatcherType=none"]
