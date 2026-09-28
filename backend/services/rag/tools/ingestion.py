from datetime import datetime
from pathlib import Path
import hashlib

from services.rag.tools.embeddings import EmbeddingService
from services.rag.tools.opensearch import OpenSearchClient


class KnowledgeIngestion:

    def __init__(self):
        self.opensearch = OpenSearchClient()
        self.embeddings = EmbeddingService()

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1200,
        overlap: int = 200,
    ) -> list[str]:

        words = text.split()

        chunks = []
        start = 0

        while start < len(words):

            end = min(
                start + chunk_size,
                len(words),
            )

            chunk = " ".join(
                words[start:end]
            )

            chunks.append(chunk)

            if end == len(words):
                break

            start = end - overlap

        return chunks

    def ingest_file(
        self,
        file_path: Path,
    ):

        # Actual knowledge base directory
        knowledge_root = (
            Path(__file__).resolve().parent.parent
            / "knowledge_base"
        )

        # Make the file path relative to knowledge_base
        relative_path = file_path.relative_to(
            knowledge_root
        )

        parts = relative_path.parts

        # Your current file is directly inside knowledge_base
        if len(parts) > 1:
            category = parts[0]
        else:
            category = "general"

        subcategory = file_path.stem

        document_id = (
            str(relative_path)
            .replace("/", "-")
            .replace("\\", "-")
            .replace(".md", "")
        )

        text = file_path.read_text(
            encoding="utf-8"
        )

        chunks = self.chunk_text(text)

        if not chunks:
            print(f"Skipping empty file: {file_path}")
            return

        title = text.splitlines()[0]

        if title.startswith("# "):
            title = title[2:].strip()

        print(f"Document: {document_id}")
        print(f"Category: {category}")
        print(f"Chunks: {len(chunks)}")

        for index, chunk in enumerate(chunks):

            raw_id = (
                f"{document_id}-"
                f"{index}-"
                f"{chunk}"
            )

            chunk_id = hashlib.sha256(
                raw_id.encode()
            ).hexdigest()

            print(
                f"Creating embedding for chunk {index}..."
            )

            embedding = self.embeddings.embed(
                chunk
            )

            print(
                f"Embedding dimensions: {len(embedding)}"
            )

            document = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "title": title,
                "category": category,
                "subcategory": subcategory,
                "content": chunk,
                "source": str(relative_path),
                "version": "1",
                "updated_at": datetime.utcnow().isoformat(),
                "embedding": embedding,
            }

            self.opensearch.index_document(
                document
            )

            print(
                f"Indexed {relative_path} "
                f"chunk {index}"
            )

    def ingest_directory(self):

        knowledge_root = (
            Path(__file__).resolve().parent.parent
            / "knowledge_base"
        )

        print(
            f"Knowledge base: {knowledge_root}"
        )

        if not knowledge_root.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {knowledge_root}"
            )

        files = list(
            knowledge_root.rglob("*.md")
        )

        print(
            f"Found {len(files)} markdown file(s)"
        )

        for file_path in files:
            print(f"Processing: {file_path}")
            self.ingest_file(file_path)

        self.opensearch.refresh()

        print("OpenSearch refresh complete.")