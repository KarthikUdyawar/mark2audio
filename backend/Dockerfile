FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    M2A_DATA_DIR=/data \
    M2A_MODEL_DIR=/models

WORKDIR /srv

# Install OS updates and runtime dependencies.
RUN apt-get update \
    && apt-get upgrade -y \
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

# Install Python project.
COPY backend/pyproject.toml ./
COPY backend/app ./app

RUN pip install --no-cache-dir ".[tts]"

# Application directories.
RUN mkdir -p /data /models \
    && chown -R app:app /srv /data

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:create", "--factory", "--host", "0.0.0.0", "--port", "8000"]
