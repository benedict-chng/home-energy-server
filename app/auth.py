"""API-key auth for the two routers. Ingest and query use separate keys."""

import secrets

from fastapi import Header, HTTPException

from app.core.config import settings


def _check(key: str | None, expected: str) -> None:
    if not key or not secrets.compare_digest(key, expected):
        raise HTTPException(status_code=401, detail="invalid or missing API key")


async def require_ingest_key(x_api_key: str | None = Header(default=None)) -> None:
    _check(x_api_key, settings.ingest_api_key)


async def require_query_key(x_api_key: str | None = Header(default=None)) -> None:
    _check(x_api_key, settings.query_api_key)
