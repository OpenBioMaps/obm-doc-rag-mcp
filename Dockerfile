# ==========================================
# 1. Builder réteg: uv és függőségek, indexelés
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# UV beállítások a gyors és determinisztikus buildhez
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Függőségek telepítése lockfile alapján (cache-elt réteg)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Forráskód, scriptek és a beépítendő hivatalos dokumentáció másolása
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY documentation/ ./documentation/
COPY README.md ./

# Projekt telepítése
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Dokumentáció előzetes indexelése a build során (beépített perzisztens index)
RUN uv run python -m scripts.build_index --docs-path documentation/official_docs/hu --output-dir /app/data/vector_store

# ==========================================
# 2. Végleges futtató réteg (Runtime)
# ==========================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Nem-root felhasználó létrehozása a biztonságos futtatáshoz
RUN useradd -m -u 1000 appuser

# Másoljuk át a virtuális környezetet, kódot, dokumentációt és a kész vektoradatbázist
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/src /app/src
COPY --from=builder --chown=appuser:appuser /app/documentation /app/documentation
COPY --from=builder --chown=appuser:appuser /app/data/vector_store /app/data/vector_store

USER appuser

EXPOSE 8000

# Alapértelmezett indítás: STDIO MCP mód (vagy felülbírálható SSE/HTTP-re)
ENTRYPOINT ["obm-mcp"]
CMD ["--transport", "stdio"]
