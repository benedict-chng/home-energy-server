#!/usr/bin/env python3
"""Post power readings to the PowerPal ingest endpoint (internal network only).

The normal case: one reading per minute, posted immediately as a single
JSON object. A bare-array flush for outage catch-up is shown at the bottom.

    pip install requests
    INGEST_API_KEY=<key> python examples/ingest_reading.py

Environment:
    POWERPAL_URL    server base URL (default http://localhost:8000)
    INGEST_API_KEY  required — the ingest key from the server's .env
"""

import os
import sys
from datetime import datetime, timezone

import requests

SERVER = os.environ.get("POWERPAL_URL", "http://localhost:8000")
API_KEY = os.environ.get("INGEST_API_KEY", "")


def sample_reading() -> dict:
    """One reading. Rules that get enforced server-side:
    - `time` must be ISO 8601 WITH a UTC offset (naive timestamps -> 422)
    - all four fields mandatory, values >= 0, unknown fields rejected
    """
    now = datetime.now(timezone.utc)
    # Melbourne local also fine: datetime.now(ZoneInfo("Australia/Melbourne"))
    return {
        "time": now.isoformat(),
        "pulses": 12,
        "kwh": 0.012,
        "average_watts": 230.5,
    }


def post_reading(reading: dict) -> dict:
    """Single-object shape — the normal 1/min case. Returns the 202 body."""
    r = requests.post(
        f"{SERVER}/api/v1/readings",
        json=reading,
        headers={"X-API-Key": API_KEY},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def post_readings(readings: list[dict]) -> dict:
    """Bare-array shape — e.g. flushing the bridge's local buffer after an
    outage. Duplicate `time` values (retries included) are skipped by the
    server, so this is safe to repeat."""
    r = requests.post(
        f"{SERVER}/api/v1/readings",
        json=readings,
        headers={"X-API-Key": API_KEY},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    if not API_KEY:
        sys.exit("Set INGEST_API_KEY (the ingest key from the server's .env)")

    # 1. Immediate single post — call this once a minute from your bridge
    result = post_reading(sample_reading())
    print(f"single: {result}")  # -> {'received': 1, 'accepted': 1, 'duplicates': 0}

    # 2. Catch-up flush (bare array) — uncomment to try
    # backlog = [sample_reading(), sample_reading()]
    # print(f"flush:  {post_readings(backlog)}")

    # 3. Idempotency demo — re-posting the exact same reading is a no-op
    # same = sample_reading()
    # print(post_reading(same))  # accepted: 1
    # print(post_reading(same))  # accepted: 0, duplicates: 1
