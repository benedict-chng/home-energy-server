# home-energy-server

FastAPI server that receives home energy readings — grid consumption from a
PowerPal BLE bridge (Raspberry Pi) and solar generation from a Fronius inverter —
stores them in Postgres/TimescaleDB, and exposes query APIs.

**Status:** v0.2.2 — LIVE on the gateway VPS (2026-10-12); 45 tests passing. Query exposure via
Cloudflare tunnel pending hostname; ingest awaits Tailscale hop from the home LAN.

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

### Solar (Fronius) — separate `solar_readings` hypertable, two fields (Ben, 18:28)

| Column          | Type             | Notes                                 |
|-----------------|------------------|---------------------------------------|
| `time`          | timestamptz (PK) | idempotency key; stored as UTC        |
| `average_watts` | double precision | ≥ 0, avg output in interval           |

Nothing else — posting extra fields (e.g. `energy_kwh`) is rejected with 422.
Own compression / 12-month retention / hourly rollup (avg watts). Grid table
untouched — the PowerPal bridge needs zero changes.

## Stack

- **App:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async) + asyncpg, Pydantic v2, pytest
- **DB:** Postgres + TimescaleDB (Community Edition) in Docker, named volume
- **Ops:** docker compose, `restart: unless-stopped`, nightly `pg_dump` (`ops/backup.sh`)
- **Migrations:** bootstrap SQL for v1; Alembic deferred until the first post-launch
  schema change (see `docs/DECISIONS.md` D7)

## API

Auth: `X-API-Key` header. Ingest and query use **separate keys**.

### `POST /api/v1/readings` — ingest (internal only)

Immediate, idempotent, returns 202. Accepts any of three shapes — all validated
identically (all fields mandatory, `>= 0`, unknown fields rejected, ISO 8601 with
UTC offset):

1. **Single reading object** — the normal case; bridge posts immediately (1/min)
2. **Bare JSON array** — e.g. flushing the bridge's local buffer after an outage
3. `{"readings": [...]}` — wrapped form, 1–1000 readings

```bash
curl -X POST http://<server>:8000/api/v1/readings \
  -H "X-API-Key: $INGEST_API_KEY" -H "Content-Type: application/json" \
  -d '{"time":"2026-10-12T16:58:00+11:00","pulses":12,"kwh":0.012,"average_watts":230.5}'
# -> {"received": 1, "accepted": 1, "duplicates": 0}
```

### `GET /api/v1/readings` — raw readings (external-facing)

Params: `from`, `to` (from inclusive, to exclusive), `limit` (default 1000, max 10000),
`offset`, `order` (`asc`/`desc`, default desc).

`from`/`to` format: **ISO 8601 with explicit UTC offset** — e.g.
`2026-10-12T00:00:00+11:00` (Melbourne) or `2026-10-12T00:00:00Z` (UTC).
Naive timestamps (no offset) are rejected with 422, same rule as ingest.
⚠️ In raw URLs `+` means space — URL-encode it (`%2B11:00`) or use `Z`, e.g.
`curl -G --data-urlencode 'from=2026-10-12T00:00:00+11:00' ...`

```
GET /api/v1/readings?from=2026-10-12T00:00:00+11:00&to=2026-10-13T00:00:00+11:00
```

### `GET /api/v1/readings/latest` — most recent reading

No params. Returns the single latest reading as an object; **404** if nothing
stored yet.

### `GET /api/v1/readings/summary` — time-bucketed aggregates

Params: `bucket` (`1m|5m|15m|1h|1d`, default `1h`), `from`, `to`. Sums pulses/kWh,
averages watts per bucket (UTC). Uses Timescale's `time_bucket`.

### Solar (Fronius) — additive, grid endpoints untouched

Same contract and three body shapes as grid, under `/api/v1/solar`:

- `POST /api/v1/solar/readings` — ingest: `time`, `average_watts` (both mandatory)
- `GET /api/v1/solar/readings?from&to&limit&offset&order`
- `GET /api/v1/solar/readings/latest`
- `GET /api/v1/solar/readings/summary?bucket=1m|5m|15m|1h|1d` — avg watts per bucket

### `GET /api/v1/energy/overview` — consumption vs generation (dashboard)

One call returns time-aligned buckets: `?from&to&bucket=1m|5m|15m|1h|1d`

```json
{"bucket": "1h", "points": [{"bucket": "2026-10-12T07:00:00Z",
  "consumed_kwh": 0.012,
  "avg_grid_watts": 230.5, "avg_solar_watts": 2450.5}]}
```

Two `time_bucket` aggregations FULL OUTER JOINed on bucket — buckets where only
one side has data still appear (other side: 0 kWh / null avg). Superimpose the
two series straight from this response. Solar is watts-only per schema; grid
keeps `consumed_kwh`.

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
DATABASE_URL=postgresql+asyncpg://homeenergy:homeenergy@localhost:5432/homeenergy \
INGEST_API_KEY=... QUERY_API_KEY=... \
uvicorn app.main:app --reload
```

## Tests

```bash
pip install -r dev-requirements.txt   # or: uv pip install ...
pytest
```

## Examples

Runnable client demos in `examples/` — only dependency is `requests`:

- `examples/ingest_reading.py` — post a single reading immediately (the 1/min case),
  with commented bare-array flush and idempotency demo
- `examples/query_readings.py` — call `/readings/latest`, `/readings` (range)
  and `/readings/summary`

```bash
pip install requests
INGEST_API_KEY=<key> python examples/ingest_reading.py
QUERY_API_KEY=<key> python examples/query_readings.py
# ENERGY_SERVER_URL defaults to http://localhost:8000
```

Both were live-tested end-to-end against the compose stack (2026-10-12):
ingest accepted, then latest / range / summary all returned the posted reading.

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
