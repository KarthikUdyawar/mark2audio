FROM python:3.12.7-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/* && useradd -m -u 1000 app
WORKDIR /srv
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir ".[tts]"
USER app
ENV M2A_DATA_DIR=/data M2A_MODEL_DIR=/models
EXPOSE 8000
CMD ["uvicorn", "app.main:create", "--factory", "--host", "0.0.0.0", "--port", "8000"]
