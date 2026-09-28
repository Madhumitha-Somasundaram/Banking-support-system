import json

import boto3

from shared.config import settings


class EmbeddingService:
    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
        )

        self.model_id = settings.BEDROCK_EMBEDDING_MODEL

    def embed(self, text: str) -> list[float]:
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "inputText": text
            }),
            contentType="application/json",
            accept="application/json",
        )

        result = json.loads(
            response["body"].read()
        )

        return result["embedding"]