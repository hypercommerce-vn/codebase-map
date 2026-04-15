# HC-AI | ticket: KMP-MCP-01
# Dockerfile — CBM + KMP Docker image
#
# 3 modes:
#   HTTP:  uvicorn (default CMD) — POST /mcp + GET /health
#   stdio: docker exec -i <ctr> python -m knowledge_memory.mcp_runner
#   CLI:   docker run --rm <img> codebase-map generate -c /workspace/...
#
# Build:
#   docker build -t codebase-map .
#
# Run (HTTP):
#   docker run -d --name cbm -v $(pwd):/workspace -p 9100:9100 codebase-map
#
# Run (CLI):
#   docker run --rm -v $(pwd):/workspace codebase-map codebase-memory summary

FROM python:3.11-slim AS base

# System deps: git (codebase-map uses git), curl (health check)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user (HC pattern)
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --create-home appuser

WORKDIR /app

# Install Python deps (leverages Docker layer cache)
COPY pyproject.toml ./
# Empty README for setuptools (pyproject.toml references it)
RUN touch README.md

COPY codebase_map/ codebase_map/
COPY knowledge_memory/ knowledge_memory/

RUN pip install --no-cache-dir ".[http]"

# Switch to non-root
USER appuser

# Vault data lives in /workspace (mounted volume)
ENV VAULT_ROOT=/workspace
EXPOSE 9100

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:9100/health || exit 1

# Default: HTTP mode
CMD ["uvicorn", "knowledge_memory.http_server:app", "--host", "0.0.0.0", "--port", "9100"]
