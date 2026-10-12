from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)
INGEST = {"X-API-Key": settings.ingest_api_key}
QUERY = {"X-API-Key": settings.query_api_key}


def _payload(**over):
    body = {
        "time": "2026-10-12T06:58:00+10:00",
        "pulses": 12,
        "kwh": 0.012,
        "average_watts": 230.5,
    }
    body.update(over)
    return {"readings": [body]}


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ingest_requires_key():
    assert client.post("/api/v1/readings", json=_payload()).status_code == 401


def test_ingest_wrong_key():
    r = client.post("/api/v1/readings", json=_payload(), headers={"X-API-Key": "nope"})
    assert r.status_code == 401


def test_ingest_invalid_payload_is_422():
    # Valid key, invalid body (naive timestamp) -> rejected before touching the DB
    r = client.post(
        "/api/v1/readings",
        json=_payload(time="2026-10-12T06:58:00"),
        headers=INGEST,
    )
    assert r.status_code == 422


def test_query_requires_key():
    assert client.get("/api/v1/readings").status_code == 401


def test_query_wrong_key():
    r = client.get("/api/v1/readings", headers={"X-API-Key": "nope"})
    assert r.status_code == 401
