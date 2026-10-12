import os

# Must be set before importing app modules (settings are read at import time).
os.environ.setdefault("INGEST_API_KEY", "test-ingest-key")
os.environ.setdefault("QUERY_API_KEY", "test-query-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://powerpal:powerpal@localhost:5432/powerpal")
