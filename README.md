# powerpal-server

FastAPI server that receives home power-usage readings from a PowerPal BLE bridge
(Raspberry Pi), stores them in Postgres/TimescaleDB, and exposes a query API.

## Stack

- **App:** Python 3.12+, FastAPI, SQLAlchemy 2.0 (async) + asyncpg, Pydantic v2, Alembic
- **DB:** Postgres + TimescaleDB (Community Edition), run in Docker with named volumes
- **Ops:** docker compose, `restart: unless-stopped`, nightly `pg_dump` backup

## API plan

- `POST /api/v1/readings` — ingest (batch, idempotent). **Internal only** (LAN / Docker network).
- `GET /api/v1/readings?from=&to=&bucket=1m|1h&device=` — query/filter. External-facing (auth required).
- `GET /healthz` — liveness.

## Layout

```
app/            FastAPI app (ingest/, query/, db/, models/, core/)
db/             migrations (Alembic), init SQL (hypertable, aggregates, retention)
ops/            backup script, deploy notes
docs/           BUILDLOG.md (every step taken), DECISIONS.md (why each choice)
docker-compose.yml
```

## Docs

- [docs/BUILDLOG.md](docs/BUILDLOG.md) — dated log of every step taken
- [docs/DECISIONS.md](docs/DECISIONS.md) — architecture decisions and rationale
