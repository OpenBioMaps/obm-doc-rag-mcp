# ==========================================
# 1. Builder stage: uv, dependencies, indexing
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# UV settings for fast and deterministic builds
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Install dependencies based on lockfile (cached layer)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy source code, scripts, and documentation to bake in
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY documentation/ ./documentation/
COPY README.md ./

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Pre-index documentation during build (baked-in persistent index)
RUN uv run python -m scripts.build_index --docs-path documentation/official_docs/hu --output-dir /app/data/vector_store

# ==========================================
# 2. Runtime stage
# ==========================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy virtual environment, source code, documentation, and pre-indexed vector store
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/src /app/src
COPY --from=builder --chown=appuser:appuser /app/documentation /app/documentation
COPY --from=builder --chown=appuser:appuser /app/data/vector_store /app/data/vector_store

USER appuser

EXPOSE 8000

# Default command: STDIO MCP mode (can be overridden to streamable-http/sse)
ENTRYPOINT ["obm-mcp"]
CMD ["--transport", "stdio"]
