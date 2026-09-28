"""RAG Service - Microservice FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.rag.api import rag as rag_api

app = FastAPI(
    title="RAG Service",
    version="1.0.0",
    description="RAG (Retrieval-Augmented Generation) microservice for banking support system",
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
app.include_router(rag_api.router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "rag-service",
    }
