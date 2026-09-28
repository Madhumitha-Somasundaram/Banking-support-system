from services.rag.tools.retriever import HybridRetriever


class RAGService:

    def __init__(self):
        self.retriever = HybridRetriever()

    def answer_question(
        self,
        query: str,
        limit: int = 5,
    ) -> dict:

        try:

            documents = self.retriever.search(
                query=query,
                limit=limit,
            )

            return {
                "status": "SUCCESS",
                "documents": documents,
            }

        except Exception as e:

            return {
                "status": "ERROR",
                "message": str(e),
                "documents": [],
            }