"""ASGI entrypoint: `uvicorn app.main:create --factory`."""

from fastapi import FastAPI

from app.api import create_app
from app.config import Settings
from app.tts import load_engine


def create() -> FastAPI:
    settings = Settings.from_env()
    return create_app(settings, load_engine(settings))
