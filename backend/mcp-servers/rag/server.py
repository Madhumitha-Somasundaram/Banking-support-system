"""
RAG MCP Server

Exposes RAG (Retrieval-Augmented Generation) operations as tools for LLMs.
Communicates with RAG Service via HTTP.

Architecture:
  MCP Server (this) :8004
      ↓ HTTP
  RAG Service :8104
      ↓
  OpenSearch (external knowledge base)
"""

from mcp.server.fastmcp import Context, FastMCP
import httpx

from shared.config import settings

mcp = FastMCP(
    "RAGServer",
    host="0.0.0.0",
    port=8004,
)


# =========================================================
# HTTP CLIENT TO RAG SERVICE
# =========================================================

def call_rag_service(
    endpoint: str,
    params: dict | None = None,
) -> dict:
    """Call the RAG Service HTTP API."""
    url = f"{settings.RAG_SERVICE_URL}{endpoint}"

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise ValueError(f"RAG Service error: {str(exc)}") from exc




@mcp.tool()
def answer_question(
    ctx: Context,
    question: str,
) -> dict:
    """
    Answer a question using RAG (Retrieval-Augmented Generation).

    Combines document retrieval with LLM generation to provide
    informed answers about banking policies and procedures.

    Parameters:
        question: Question to answer

    Returns:
        {
            "status": str,
            "answer": str,
            "sources": [
                {
                    "source": str,
                    "excerpt": str
                }
            ]
        }
    """
    return call_rag_service(
        endpoint="/retrieval/answer",
        params={"query": question},
    )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
