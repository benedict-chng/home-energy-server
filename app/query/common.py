"""Shared helpers for query routers."""

from datetime import datetime

from fastapi import HTTPException

BUCKETS = {"1m": "1 minute", "5m": "5 minutes", "15m": "15 minutes", "1h": "1 hour", "1d": "1 day"}


def require_utc_offset(name: str, v: datetime | None) -> datetime | None:
    """Same rule as ingest: timestamps must carry an explicit UTC offset,
    so Melbourne local time is never silently read as UTC."""
    if v is not None and (v.tzinfo is None or v.tzinfo.utcoffset(v) is None):
        raise HTTPException(
            status_code=422,
            detail=f"'{name}' must be ISO 8601 with a UTC offset, e.g. 2026-10-12T00:00:00+11:00",
        )
    return v


def validate_range(from_: datetime | None, to: datetime | None) -> None:
    if from_ and to and from_ >= to:
        raise HTTPException(status_code=422, detail="'from' must be earlier than 'to'")
