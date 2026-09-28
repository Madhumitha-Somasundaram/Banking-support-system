"""Account Service - Microservice FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.account.api import account as account_api

app = FastAPI(
    title="Account Service",
    version="1.0.0",
    description="Account microservice for banking support system",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(account_api.router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "account-service",
    }
