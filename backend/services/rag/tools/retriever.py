from services.rag.tools.embeddings import EmbeddingService
from services.rag.tools.opensearch import OpenSearchClient


class HybridRetriever:
    def __init__(self):
        self.opensearch = OpenSearchClient()
        self.embeddings = EmbeddingService()

    def bm25_search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:

        response = self.opensearch.client.search(
            index=self.opensearch.index_name,
            body={
                "size": limit,
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "title^3",
                            "content^2",
                            "category",
                            "subcategory",
                        ]
                    }
                }
            },
        )

        return [
            hit["_source"]
            for hit in response["hits"]["hits"]
        ]

    def vector_search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:

        vector = self.embeddings.embed(query)

        response = self.opensearch.client.search(
            index=self.opensearch.index_name,
            body={
                "size": limit,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": vector,
                            "k": limit,
                        }
                    }
                }
            },
        )

        return [
            hit["_source"]
            for hit in response["hits"]["hits"]
        ]

    def reciprocal_rank_fusion(
        self,
        bm25_results: list[dict],
        vector_results: list[dict],
        limit: int = 5,
        k: int = 60,
    ) -> list[dict]:

        scores = {}
        documents = {}

        for rank, document in enumerate(
            bm25_results,
            start=1,
        ):
            chunk_id = document["chunk_id"]

            documents[chunk_id] = document

            scores[chunk_id] = (
                scores.get(chunk_id, 0)
                + 1 / (k + rank)
            )

        for rank, document in enumerate(
            vector_results,
            start=1,
        ):
            chunk_id = document["chunk_id"]

            documents[chunk_id] = document

            scores[chunk_id] = (
                scores.get(chunk_id, 0)
                + 1 / (k + rank)
            )

        ranked_ids = sorted(
            scores,
            key=scores.get,
            reverse=True,
        )

        return [
            documents[chunk_id]
            for chunk_id in ranked_ids[:limit]
        ]

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        bm25_results = self.bm25_search(
            query=query,
            limit=10,
        )

        vector_results = self.vector_search(
            query=query,
            limit=10,
        )

        return self.reciprocal_rank_fusion(
            bm25_results=bm25_results,
            vector_results=vector_results,
            limit=limit,
        )