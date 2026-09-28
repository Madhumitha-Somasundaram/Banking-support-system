from pathlib import Path

from app.rag.ingestion import KnowledgeIngestion


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Knowledge base file
KNOWLEDGE_FILE = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "knowledge_base"
    / "knowledge.md"
)


# Check file exists
if not KNOWLEDGE_FILE.exists():
    raise FileNotFoundError(
        f"Knowledge base file not found: {KNOWLEDGE_FILE}"
    )


print(f"Found knowledge file: {KNOWLEDGE_FILE}")


# Create ingestion service
ingestion = KnowledgeIngestion()


# Ingest the file
ingestion.ingest_file(KNOWLEDGE_FILE)


# Refresh OpenSearch
ingestion.opensearch.refresh()


print("Knowledge ingestion complete.")