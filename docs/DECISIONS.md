# Decisions

Each decision: what we chose, why, and what we rejected.

## D1 — Database: Postgres + TimescaleDB (Community Edition) in Docker

- **Why:** workload is classic time-series (small frequent writes, time-range + aggregation reads). Hypertables, continuous aggregates (1-min/hourly rollups), columnar compression (~90%), retention policies come free. Same SQL/driver/tooling as plain Postgres.
- **Licensing:** Community Edition is under the Timescale License — free to self-host; restriction only applies to offering it as a managed DB service. Apache-2 edition exists if strict FOSS is ever required. Verified 2026-10-12 (tigerdata.com/legal/licenses).
- **Rejected:** SQLite (sufficient at ~20k rows/day but weaker analytics ergonomics), InfluxDB (licensing/Flux churn).

## D2 — One FastAPI app, two routers

- `ingest` router (`POST /api/v1/readings`): batch, idempotent upsert on `(device_id, ts)`, returns 202 fast, no heavy work inline. Internal only.
- `query` router (`GET /api/v1/readings`): time-range + bucket filters, pagination. External-facing, separate read-only API key.
- **Why one app:** simpler ops for a home server; separation enforced by network (ingest not published) + distinct tokens per router, so accidental exposure isn't fatal.

## D3 — Durability

- Docker **named volumes** for Postgres data (survives restarts/upgrades; never `compose down -v` casually).
- `restart: unless-stopped` on all services.
- Postgres WAL makes it crash-safe on power loss.
- Nightly `pg_dump` to a second location (disk/NAS) — restarts don't protect against disk death.
- Bridge already buffers readings, so server downtime doesn't lose data.

## D4 — External exposure: Tailscale recommended (final call pending)

- Query endpoint reachable over tailnet; nothing published to the internet. Public exposure (Caddy + TLS + API key) only if a third-party client needs it.
- Status: **awaiting Ben's call.**

## D5 — Step documentation: this repo

- Every step logged in `docs/BUILDLOG.md` (dated, newest first), decisions in this file, one logical commit per step.
