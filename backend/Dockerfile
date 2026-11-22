FROM python:3.12.7-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    M2A_DATA_DIR=/data \
    M2A_MODEL_DIR=/models

WORKDIR /srv

# Install runtime dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root application user.
RUN useradd \
    --create-home \
    --uid 1000 \
    --shell /usr/sbin/nologin \
    app

# Install locked dependencies (backend/uv.lock), then the app source.
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --extra tts --no-install-project
COPY backend/app ./app

# Application directories.
RUN mkdir -p /data /models \
    && chown -R app:app /srv /data

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:create", "--factory", "--host", "0.0.0.0", "--port", "8000"]
