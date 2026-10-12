#!/usr/bin/env python3
"""Query examples: latest reading, raw range, and bucketed summary.

    pip install requests
    QUERY_API_KEY=<key> python examples/query_readings.py

Environment:
    POWERPAL_URL    server base URL (default http://localhost:8000)
    QUERY_API_KEY   required — the (separate) read-only key from the server's .env
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import requests

SERVER = os.environ.get("POWERPAL_URL", "http://localhost:8000")
API_KEY = os.environ.get("QUERY_API_KEY", "")
HEADERS = {"X-API-Key": API_KEY}


def latest() -> dict | None:
    """GET /api/v1/readings/latest — newest reading, no params. None if empty."""
    r = requests.get(f"{SERVER}/api/v1/readings/latest", headers=HEADERS, timeout=10)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def raw_range(start: datetime, end: datetime, limit: int = 1000, order: str = "asc") -> dict:
    """GET /api/v1/readings — from (inclusive) / to (exclusive).

    `start`/`end` must be timezone-aware; .isoformat() then produces the
    required explicit offset. Passing them via `params=` gets the '+' in
    the offset URL-encoded for free (a hand-built URL would break: raw
    '+' means space).
    """
    r = requests.get(
        f"{SERVER}/api/v1/readings",
        params={
            "from": start.isoformat(),
            "to": end.isoformat(),
            "limit": limit,
            "order": order,
        },
        headers=HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()  # {"count": n, "readings": [...]}


def summary(start: datetime, end: datetime, bucket: str = "1h") -> dict:
    """GET /api/v1/readings/summary — bucket: 1m|5m|15m|1h|1d (UTC buckets).
    Returns per-bucket sum(pulses), sum(kwh), avg(average_watts)."""
    r = requests.get(
        f"{SERVER}/api/v1/readings/summary",
        params={"from": start.isoformat(), "to": end.isoformat(), "bucket": bucket},
        headers=HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()  # {"bucket": "1h", "points": [...]}


if __name__ == "__main__":
    if not API_KEY:
        sys.exit("Set QUERY_API_KEY (the query key from the server's .env)")

    # 1. Latest — cheapest way to show "right now" on a dashboard
    print(f"latest:  {latest()}")  # None (404) if nothing stored yet

    # 2. Last 24 hours of raw readings, oldest first
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    page = raw_range(start, end)
    print(f"range:   {page['count']} reading(s) in the last 24h")
    for row in page["readings"][:5]:
        print(f"         {row}")

    # 3. Hourly summary for the same window (swap bucket="1d" for daily energy)
    print(f"summary: {summary(start, end, bucket='1h')}")
