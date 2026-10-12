# Build Log

Dated log of every step taken on this project. Newest first.

## 2026-10-12 (afternoon)

- **~17:00 — Schema received and locked in.** Ben's exact schema: `time` (datetime), `pulses` (int), `kwh` (float), `average_watts` (float); all four mandatory. Repo stays **local only** — Ben will push to remote himself at a stage of his choosing.
- **~17:05 — v0.1.0 scaffold built, schema baked in:**
  - FastAPI app: ingest router (batch POST, idempotent `ON CONFLICT (time) DO NOTHING`, 202) + query router (raw range reads; `time_bucket` summary endpoint) + `/healthz` + `/readyz`.
  - Separate `X-API-Key` per router (ingest key vs read-only query key).
  - Pydantic v2 validation: all fields mandatory, `>= 0` checks, unknown fields rejected, **naive timestamps rejected** (must carry UTC offset), normalised to UTC on the way in.
  - SQLAlchemy 2.0 async model matching the schema exactly; `time` is the PK so bridge retries can't duplicate rows.
  - Dockerfile + docker-compose: `timescale/timescaledb:latest-pg16`, named volume, `restart: unless-stopped`, DB port loopback-only.
  - `db/init/`: 01 base schema; 02 Timescale policies (hypertable, compress >7 days, raw retention 12 months, hourly continuous aggregate kept forever).
  - `ops/backup.sh`: nightly `pg_dump` to `backups/`, 14-day retention, cron line in header.
- **~17:10 — Test runs, with fixes (all documented):**
  1. `python3 -m venv` failed — host lacks `python3-venv`/ensurepip → switched to `uv venv` (already installed).
  2. `ImportError: cannot import name 'DoublePrecision'` — not a real SQLAlchemy top-level name → replaced with generic `Double` (compiles to DOUBLE PRECISION on PG).
  3. Tests couldn't import `app` package → added `pyproject.toml` with `[tool.pytest.ini_options] pythonpath = ["."]`.
  - Final result: **13 passed** (schema validation incl. naive-time/missing-field/extra-field/negative rejections, UTC normalisation, batch bounds, auth 401 paths, healthz, 422 before DB).
- **~17:15 — Committed v0.1.0.** README rewritten to match built reality; D6/D7 added to DECISIONS.

## 2026-10-12 (midday)

- **16:35 — Architecture agreed (chat, Telegram).** Requirements: FastAPI server; ingest endpoint internal-only from existing PowerPal BLE bridge (Raspberry Pi); external query endpoint with filtering; durable storage.
- **16:42 — DB choice + licensing reviewed.** TimescaleDB explained and license checked live (Apache-2 edition vs Community/TSL; free to self-host either way). Confirmed: Postgres + TimescaleDB Community in Docker.
- **16:43 — Durability plan confirmed.** Docker named volumes, `restart: unless-stopped`, WAL crash-safety, nightly `pg_dump`. Setup must survive restarts/reboots.
- **16:48 — Repo initialised.** Created this repository with docs skeleton: README, BUILDLOG (this file), DECISIONS. Initial commit. Remote hosting deferred — Ben chose to keep it local for now.
