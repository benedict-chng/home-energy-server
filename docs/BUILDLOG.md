# Build Log

Dated log of every step taken on this project. Newest first.

## 2026-10-12 (afternoon)

- **19:08 — Project renamed: `powerpal-server` → `home-energy-server` (Ben's call) — v0.2.2.** It now ingests two sources, so the name generalised. Changed: directory, pyproject name/description, FastAPI title ("Home Energy Server"), DB user/db defaults (`homeenergy`) across compose + .env.example + config fallback + tests conftest, backup dump prefix (`home-energy-*.sql.gz`), example env var `POWERPAL_URL` → `ENERGY_SERVER_URL`. Kept: table names (`readings`, `solar_readings`), endpoint paths, device names (PowerPal, Fronius) where they describe data sources, and this log's historical entries. Venv recreated at the new path. Suite: **45 passed**. Committed as v0.2.2.

- **18:28 — Solar schema correction (Ben): TWO fields only — `time` + `average_watts`.** Dropped `energy_kwh`/`power_watts` everywhere: model, schemas, ingest rows, solar summary (avg watts per bucket), Timescale init SQL + hourly rollup, and the energy overview (`generated_kwh` removed — solar is watts-only; grid keeps `consumed_kwh` + `avg_grid_watts`). Regression tests added: posting `energy_kwh` to solar → 422 (extra-field rejection). Suite: **45 passed**. Re-verified live against a fresh compose stack. Committed as v0.2.1.

- **18:14 — Solar (Fronius) support added (Ben's request) — v0.2.0.** Separate `solar_readings` hypertable (`time` PK, `power_watts`, `energy_kwh` — all mandatory), mirrored endpoints under `/api/v1/solar/*` (same three ingest body shapes, same validation/idempotency/UTC-offset rules), plus **`GET /api/v1/energy/overview?from&to&bucket=`** — grid consumption vs solar generation, two `time_bucket` aggregations FULL OUTER JOINed on bucket, one call per dashboard superimposition. **Ben's question answered: grid endpoints untouched** — additive only, PowerPal bridge needs zero changes. Refactors to share one source of truth for the rules: `app/schemas/common.py` (UTC-offset + body-shape normalisation), `app/ingest/common.py` (`insert_idempotent`), `app/query/common.py` (BUCKETS/range/offset helpers) — behavior unchanged. Suite: **44 passed**. Live-tested against compose on this host: grid + solar ingest accepted into the same hour bucket → overview returned one aligned point (`consumed_kwh: 0.012, generated_kwh: 0.24`), solar + grid `/latest` both correct, proving the solar init SQL and the FULL OUTER JOIN path on real Timescale. Stack/volume/.env torn down. Committed as v0.2.0.

- **17:34 — Example clients added (Ben's request) and live-tested end-to-end.** New `examples/`: `ingest_reading.py` (single-object immediate post, commented bare-array flush + idempotency demo) and `query_readings.py` (`/latest`, `/readings` range, `/readings/summary`), using `requests` with env-based config (`POWERPAL_URL`, `INGEST_API_KEY`, `QUERY_API_KEY`). Verified against a real compose stack spun up on this host: healthz/readyz OK → ingest `{'received': 1, 'accepted': 1, 'duplicates': 0}` → latest, range and summary all returned the posted reading. That also proves the Timescale init SQL and the `time_bucket` summary path work on a real DB, not just unit tests. Throwaway stack, named volume and test `.env` torn down afterwards. Suite unchanged: **24 passed**. Committed as v0.1.4.

- **17:28 — `from`/`to` format question (Ben) → gap found and closed:** query params weren't enforcing the UTC-offset rule that ingest has. Added `_require_utc_offset` to `/readings` and `/readings/summary` — naive timestamps now 422 with a pointer to the expected format. README documents the format + the raw-URL `+`-means-space gotcha (URL-encode as `%2B` or use `Z`). Suite: **24 passed**. Committed as v0.1.3.

- **17:26 — `GET /api/v1/readings/latest` added (Ben's request):** returns just the most recent reading — no from/to/limit/order needed. 404 with a clear message when the DB is still empty. Query-key auth applies. Suite: **22 passed**. Committed as v0.1.2.

- **17:14 — Ingest feedback from Ben:** he prefers immediate posting, not batching — it's only one reading per minute. Generalised `POST /api/v1/readings` to accept a **single JSON object** (now the documented primary mode), a **bare array** (outage catch-up), or the wrapped `{"readings": [...]}` form — one `IngestPayload` validator normalises all three, same validation and idempotency. New schema + API tests for each shape (incl. bad readings inside bare lists → 422): **20 passed**. Test-side gotchas fixed en route and worth remembering: `**` can't unpack a list, and Pydantic v2 `BaseModel.__init__` takes only kwargs — pass non-dict bodies via `Model.model_validate([...])`. Committed as v0.1.1.

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
