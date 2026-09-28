import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

from backend.app.shared.config import settings


# Load environment variables
load_dotenv()


# S3 configuration
BUCKET = settings.KNOWLEDGE_S3_BUCKET
PREFIX = os.environ.get("KNOWLEDGE_S3_PREFIX", "knowledge/")


# Unified knowledge base file
ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_FILE = ROOT / "backend"/"app" / "knowledge_base" / "knowledge.md"


# Create S3 client
s3 = boto3.client("s3")


# Check file exists
if not KNOWLEDGE_FILE.exists():
    raise FileNotFoundError(
        f"Knowledge base file not found: {KNOWLEDGE_FILE}"
    )


# Build S3 key
KEY = (
    PREFIX.rstrip("/")
    + "/"
    + KNOWLEDGE_FILE.name
)


print(
    f"Uploading {KNOWLEDGE_FILE} -> "
    f"s3://{BUCKET}/{KEY}"
)


# Upload
s3.upload_file(
    str(KNOWLEDGE_FILE),
    BUCKET,
    KEY,
)


print("Knowledge upload complete.")