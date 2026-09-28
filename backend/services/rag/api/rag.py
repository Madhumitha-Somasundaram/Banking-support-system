"""RAG Service REST API endpoints."""

from fastapi import APIRouter, Query

from services.rag.service.rag_service import RAGService

router = APIRouter(prefix="/retrieval", tags=["rag"])

rag_service = RAGService()


@router.post("/answer")
def answer_question(
    query: str = Query(..., description="Question to answer"),
):
    """
    Answer a question using RAG (Retrieval + Generation).

    Args:
        query: Question to answer

    Returns:
        Generated answer with source documents
    """
    return rag_service.answer_question(query=query)
