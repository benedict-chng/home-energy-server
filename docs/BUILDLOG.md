# Build Log

Dated log of every step taken on this project. Newest first.

## 2026-10-12

- **16:35 — Architecture agreed (chat, Telegram).** Requirements: FastAPI server; ingest endpoint internal-only from existing PowerPal BLE bridge (Raspberry Pi); external query endpoint with filtering; durable storage.
- **16:42 — DB choice + licensing reviewed.** TimescaleDB explained and license checked live (Apache-2 edition vs Community/TSL; free to self-host either way). Confirmed: Postgres + TimescaleDB Community in Docker.
- **16:43 — Durability plan confirmed.** Docker named volumes, `restart: unless-stopped`, WAL crash-safety, nightly `pg_dump`. Setup must survive restarts/reboots.
- **16:48 — Repo initialised.** Created this repository with docs skeleton: README, BUILDLOG (this file), DECISIONS. Initial commit. Remote hosting (GitHub) pending — choosing access method (Control UI GitHub connect vs fine-grained PAT).
