
from app.rag.opensearch import OpenSearchClient


client = OpenSearchClient()

if client.index_exists():
    print("Index already exists.")
else:
    client.create_index()
    print("OpenSearch index created.")