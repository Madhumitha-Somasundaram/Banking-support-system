import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from shared.config import settings


class OpenSearchClient:
    def __init__(self):
        credentials = boto3.Session().get_credentials()

        if credentials is None:
            raise RuntimeError(
                "AWS credentials not found. Configure AWS credentials first."
            )

        credentials = credentials.get_frozen_credentials()

        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            "us-east-1",
            "es",
            session_token=credentials.token,
        )

        host = settings.OPENSEARCH_URL.replace("https://", "").rstrip("/")

        self.client = OpenSearch(
            hosts=[{
                "host": host,
                "port": 443,
            }],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )

        self.index_name = settings.OPENSEARCH_INDEX

    def index_exists(self) -> bool:
        return self.client.indices.exists(
            index=self.index_name
        )

    def create_index(self):
        if self.index_exists():
            print(f"Index '{self.index_name}' already exists.")
            return

        body = {
            "settings": {
                "index": {
                    "knn": True
                }
            },
            "mappings": {
                "properties": {
                    "chunk_id": {
                        "type": "keyword"
                    },
                    "document_id": {
                        "type": "keyword"
                    },
                    "title": {
                        "type": "text"
                    },
                    "category": {
                        "type": "keyword"
                    },
                    "subcategory": {
                        "type": "keyword"
                    },
                    "content": {
                        "type": "text"
                    },
                    "source": {
                        "type": "keyword"
                    },
                    "version": {
                        "type": "keyword"
                    },
                    "updated_at": {
                        "type": "date"
                    },
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1024
                    }
                }
            }
        }

        self.client.indices.create(
            index=self.index_name,
            body=body,
        )

        print(f"Created index '{self.index_name}'.")

    def index_document(self, document: dict):
        self.client.index(
            index=self.index_name,
            id=document["chunk_id"],
            body=document,
        )

    def refresh(self):
        self.client.indices.refresh(
            index=self.index_name
        )