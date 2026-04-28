FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_COMPILE_BYTECODE=1 \
    UV_CACHE_DIR=/uv-cache

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --no-install-project

COPY . .

RUN uv sync --no-dev

RUN rm -rf /uv-cache/ root/.cache/pip

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]