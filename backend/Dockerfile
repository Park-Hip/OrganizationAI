# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Bring in uv for reproducible dependency installation.
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

WORKDIR /app

# Install dependencies first so source changes reuse this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application and migration sources, then install the project itself.
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY README.md ./

RUN uv sync --frozen --no-dev --no-editable

# Run as a non-root user; secrets arrive via environment at runtime only.
RUN groupadd --system app && useradd --system --gid app --create-home app
USER app

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]