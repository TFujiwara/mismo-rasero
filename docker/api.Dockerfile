FROM python:3.11-slim

WORKDIR /repo
RUN pip install --no-cache-dir uv

# cache de dependencias del workspace
COPY pyproject.toml uv.lock* ./
COPY packages/api/pyproject.toml packages/api/pyproject.toml
COPY packages/scrapers/pyproject.toml packages/scrapers/pyproject.toml
COPY packages/disarm/pyproject.toml packages/disarm/pyproject.toml
COPY packages/video/pyproject.toml packages/video/pyproject.toml
RUN uv sync --no-install-project || uv sync

COPY pyproject.toml uv.lock* ./
COPY packages/ packages/
RUN uv sync

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
