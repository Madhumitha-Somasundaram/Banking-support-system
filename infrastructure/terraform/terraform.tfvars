db_password    = "Banking-support-2026"
opensearch_url = "https://search-banking-support-search-oqetiwzw75hig3fdyq42kuwcou.us-east-1.es.amazonaws.com"

knowledge_s3_bucket = "banking-support-knowledge"

bedrock_embedding_model = "amazon.titan-embed-text-v2:0"

public_subnets = [
  "subnet-0a3f8d4d1d6c4fdc8",  # us-east-1a
  "subnet-0592ceacff8538a36"   # us-east-1b
]

private_subnets = [
  "subnet-01203b30ee3e6c17e",
  "subnet-043b8b46e1a09b4d9"
]