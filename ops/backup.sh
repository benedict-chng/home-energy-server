#!/usr/bin/env bash
# Nightly pg_dump of the home-energy-server DB. Restarts don't protect against disk death;
# keep a copy of backups/ on another disk or NAS.
#
# Cron example (3:15am daily):
#   15 3 * * * /path/to/home-energy-server/ops/backup.sh >> /path/to/home-energy-server/backups/backup.log 2>&1
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${ROOT}/backups"
KEEP_DAYS=14

# shellcheck disable=SC1091
[ -f "${ROOT}/.env" ] && set -a && . "${ROOT}/.env" && set +a
PGUSER="${POSTGRES_USER:-homeenergy}"
PGDATABASE="${POSTGRES_DB:-homeenergy}"

mkdir -p "${BACKUP_DIR}"
OUT="${BACKUP_DIR}/home-energy-$(date +%F).sql.gz"

docker compose -f "${ROOT}/docker-compose.yml" exec -T db \
    pg_dump -U "${PGUSER}" "${PGDATABASE}" | gzip > "${OUT}"

find "${BACKUP_DIR}" -name 'home-energy-*.sql.gz' -mtime +"${KEEP_DAYS}" -delete
echo "$(date -Is) wrote ${OUT}"
