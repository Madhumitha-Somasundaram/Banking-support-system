"""Transaction Service - Microservice FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.transaction.api import transaction as transaction_api

app = FastAPI(
    title="Transaction Service",
    version="1.0.0",
    description="Transaction microservice for banking support system",
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
app.include_router(transaction_api.router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Transaction-service",
    }
