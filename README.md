# powerpal-server

FastAPI server that receives home power-usage readings from a PowerPal BLE bridge
(Raspberry Pi), stores them in Postgres/TimescaleDB, and exposes a query API.

**Status:** v0.1.0 — scaffold complete, 13 tests passing. Local only; pushed to
remote once Ben says go.

## Data schema (as specified, all fields mandatory)

| Column          | Type             | Notes                          |
|-----------------|------------------|--------------------------------|
| `time`          | timestamptz (PK) | idempotency key; stored as UTC |
| `pulses`        | integer          | ≥ 0                            |
| `kwh`           | double precision | ≥ 0                            |
| `average_watts` | double precision | ≥ 0                            |

- Bridge retries can never duplicate rows (`ON CONFLICT (time) DO NOTHING`).
- API requires ISO 8601 **with UTC offset** — naive timestamps are rejected (422).
- Single-device design: no `device_id` until a second meter exists.
- Timescale extras: hypertable, compression after 7 days, raw data kept 12 months,
  hourly continuous aggregate kept forever (`db/init/02_timescale.sql`).

## Stack

- **App:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async) + asyncpg, Pydantic v2, pytest
- **DB:** Postgres + TimescaleDB (Community Edition) in Docker, named volume
- **Ops:** docker compose, `restart: unless-stopped`, nightly `pg_dump` (`ops/backup.sh`)
- **Migrations:** bootstrap SQL for v1; Alembic deferred until the first post-launch
  schema change (see `docs/DECISIONS.md` D7)

## API

Auth: `X-API-Key` header. Ingest and query use **separate keys**.

### `POST /api/v1/readings` — ingest (internal only)

Batch, idempotent, returns 202. 1–1000 readings per call; unknown fields rejected.

```bash
curl -X POST http://<server>:8000/api/v1/readings \
  -H "X-API-Key: $INGEST_API_KEY" -H "Content-Type: application/json" \
  -d '{"readings":[{"time":"2026-10-12T16:58:00+11:00","pulses":12,"kwh":0.012,"average_watts":230.5}]}'
# -> {"received": 1, "accepted": 1, "duplicates": 0}
```

### `GET /api/v1/readings` — raw readings (external-facing)

Params: `from`, `to` (from inclusive, to exclusive), `limit` (default 1000, max 10000),
`offset`, `order` (`asc`/`desc`, default desc).

```
GET /api/v1/readings?from=2026-10-12T00:00:00+11:00&to=2026-10-13T00:00:00+11:00
```

### `GET /api/v1/readings/summary` — time-bucketed aggregates

Params: `bucket` (`1m|5m|15m|1h|1d`, default `1h`), `from`, `to`. Sums pulses/kWh,
averages watts per bucket (UTC). Uses Timescale's `time_bucket`.

### Ops

`GET /healthz` (process liveness), `GET /readyz` (checks DB connectivity). No auth.

## Quickstart

```bash
cp .env.example .env          # set POSTGRES_PASSWORD + both API keys (openssl rand -hex 32)
docker compose up -d --build
curl -s localhost:8000/healthz
```

Local dev without Docker: create the DB, run `db/init/01_schema.sql` (add
`02_timescale.sql` only on TimescaleDB), then:

```bash
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://powerpal:pass@localhost:5432/powerpal \
INGEST_API_KEY=... QUERY_API_KEY=... \
uvicorn app.main:app --reload
```

## Tests

```bash
pip install -r dev-requirements.txt   # or: uv pip install ...
pytest
```

## Backups

`ops/backup.sh` does a nightly `pg_dump` (gzip, 14-day retention). Cron line is in
the script header. **Copy `backups/` off the machine** — restarts don't protect
against disk death.

## Layout

```
app/               FastAPI app
  ingest/          POST /api/v1/readings (internal only)
  query/           GET /api/v1/readings[/summary] (external-facing)
  models/          SQLAlchemy models
  schemas/         Pydantic schemas (all fields mandatory)
  core/            config, async engine/session
db/init/           bootstrap SQL (01 base schema, 02 Timescale policies)
ops/               backup script
tests/             pytest suite
docs/              BUILDLOG.md (every step taken), DECISIONS.md (why each choice)
```

## Docs

- [docs/BUILDLOG.md](docs/BUILDLOG.md) — dated log of every step taken
- [docs/DECISIONS.md](docs/DECISIONS.md) — architecture decisions and rationale
