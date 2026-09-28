from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.api.auth import router as auth_router
from app.chat.api.chat import router as chat_router
from app.api.health import router as health_router

from app.db.database import Base, engine

# Make sure all models are registered.
from app.chat.models.conversations import Conversation
from app.chat.models.messages import Message
from app.chat.models.jobs import AgentJob

from shared.config import settings
from shared.tracing import (
    init_tracing,
    instrument_fastapi,
)


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="Banking Support AI",
    version="1.0.0",
    description=(
        "AI-powered banking support system "
        "with security, RBAC, and critical task approval"
    ),
)

init_tracing(
    service_name="banking-main-backend",
)

instrument_fastapi(
    app
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_router
)

app.include_router(
    auth_router
)

app.include_router(
    chat_router
)