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


def test_ingest_single_object_invalid_is_422():
    # Immediate-post shape (single object, no wrapper)
    body = {
        "time": "2026-10-12T06:58:00",
        "pulses": 12,
        "kwh": 0.012,
        "average_watts": 230.5,
    }
    r = client.post("/api/v1/readings", json=body, headers=INGEST)
    assert r.status_code == 422


def test_ingest_bare_list_invalid_is_422():
    # Buffer-flush shape (bare array, no wrapper)
    body = {
        "time": "2026-10-12T06:58:00+10:00",
        "pulses": -1,
        "kwh": 0.012,
        "average_watts": 230.5,
    }
    r = client.post("/api/v1/readings", json=[body], headers=INGEST)
    assert r.status_code == 422


def test_query_requires_key():
    assert client.get("/api/v1/readings").status_code == 401


def test_query_wrong_key():
    r = client.get("/api/v1/readings", headers={"X-API-Key": "nope"})
    assert r.status_code == 401


def test_latest_requires_key():
    assert client.get("/api/v1/readings/latest").status_code == 401


def test_latest_wrong_key():
    r = client.get("/api/v1/readings/latest", headers={"X-API-Key": "nope"})
    assert r.status_code == 401


def test_readings_naive_from_is_422():
    # Query params follow the same rule as ingest: explicit UTC offset required
    r = client.get(
        "/api/v1/readings",
        params={"from": "2026-10-12T00:00:00"},
        headers=QUERY,
    )
    assert r.status_code == 422


def test_summary_naive_from_is_422():
    r = client.get(
        "/api/v1/readings/summary",
        params={"from": "2026-10-12T00:00:00"},
        headers=QUERY,
    )
    assert r.status_code == 422


# --- Solar endpoints (Fronius) — additive, grid endpoints untouched ---

SOLAR = {
    "time": "2026-10-12T12:00:00+10:00",
    "power_watts": 2450.5,
    "energy_kwh": 0.24,
}


def test_solar_ingest_requires_key():
    assert client.post("/api/v1/solar/readings", json=SOLAR).status_code == 401


def test_solar_ingest_wrong_key():
    r = client.post("/api/v1/solar/readings", json=SOLAR, headers={"X-API-Key": "***"})
    assert r.status_code == 401


def test_solar_ingest_invalid_is_422():
    body = {**SOLAR, "time": "2026-10-12T12:00:00"}  # naive timestamp
    r = client.post("/api/v1/solar/readings", json=body, headers=INGEST)
    assert r.status_code == 422


def test_solar_ingest_bare_list_invalid_is_422():
    r = client.post(
        "/api/v1/solar/readings",
        json=[{**SOLAR, "energy_kwh": -1}],
        headers=INGEST,
    )
    assert r.status_code == 422


def test_solar_query_requires_key():
    assert client.get("/api/v1/solar/readings").status_code == 401


def test_solar_latest_requires_key():
    assert client.get("/api/v1/solar/readings/latest").status_code == 401


def test_solar_summary_requires_key():
    assert client.get("/api/v1/solar/readings/summary").status_code == 401


def test_solar_readings_naive_from_is_422():
    r = client.get(
        "/api/v1/solar/readings",
        params={"from": "2026-10-12T00:00:00"},
        headers=QUERY,
    )
    assert r.status_code == 422


def test_energy_overview_requires_key():
    assert client.get("/api/v1/energy/overview").status_code == 401


def test_energy_overview_naive_from_is_422():
    r = client.get(
        "/api/v1/energy/overview",
        params={"from": "2026-10-12T00:00:00"},
        headers=QUERY,
    )
    assert r.status_code == 422
