from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str | None = None
    ACCOUNT_DATABASE_URL: str | None = None
    TRANSACTION_DATABASE_URL: str | None = None
    CARD_DATABASE_URL: str | None = None
    LANGGRAPH_CHECKPOINT_DATABASE_URL: str | None = None

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    ACCOUNT_MCP_URL: str
    ACCOUNT_SERVICE_URL: str
    ACCOUNT_AGENT_URL: str

    TRANSACTION_MCP_URL: str
    TRANSACTION_SERVICE_URL: str
    TRANSACTION_AGENT_URL: str

    CARD_MCP_URL: str
    CARD_SERVICE_URL: str
    CARD_AGENT_URL: str

    RAG_MCP_URL: str
    RAG_SERVICE_URL: str
    RAG_AGENT_URL: str

    OPENSEARCH_URL: str
    OPENSEARCH_INDEX: str

    KNOWLEDGE_S3_BUCKET: str
    KNOWLEDGE_S3_PREFIX: str

    BEDROCK_REGION: str
    BEDROCK_EMBEDDING_MODEL: str
    CORS_ORIGINS: str = "http://localhost:3000,https://payanams.xyz"
    AGENT_QUEUE_URL: str
    
    class Config:
        env_file = BASE_DIR / ".env"


settings = Settings()