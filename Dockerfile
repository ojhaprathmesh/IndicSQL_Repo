# IndicSQL Production Container Image
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    INDICSQL_DEVICE=cpu \
    INDICSQL_OFFLINE=1

WORKDIR /app

# Install system dependencies (build essentials for DuckDB and wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for rapid, deterministic package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project manifests
COPY pyproject.toml README.md ./

# Install project dependencies
RUN uv pip install --system -e .

# Copy application source, data stores, and catalogs
COPY indicsql/ ./indicsql/
COPY data/parquet_stores/ ./data/parquet_stores/
COPY data/ndap_catalogs/ ./data/ndap_catalogs/
COPY models/lora_weights/ ./models/lora_weights/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "indicsql.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
