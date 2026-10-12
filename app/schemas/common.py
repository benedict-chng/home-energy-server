"""Shared schema helpers — one source of truth for the ingest rules.

Rules (identical for grid and solar):
- `time` must be ISO 8601 WITH an explicit UTC offset, stored normalised to UTC
- ingest body accepts a single reading object (immediate post), a bare JSON
  list (outage catch-up), or the wrapped {"readings": [...]} form
"""

from datetime import datetime, timezone


def require_utc_offset(v: datetime) -> datetime:
    if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
        raise ValueError(
            "time must be ISO 8601 with a UTC offset, e.g. 2026-10-12T06:58:00+10:00"
        )
    return v.astimezone(timezone.utc)


def accept_single_object_or_list(data: object) -> object:
    if isinstance(data, dict) and "readings" not in data:
        return {"readings": [data]}
    if isinstance(data, list):
        return {"readings": data}
    return data
