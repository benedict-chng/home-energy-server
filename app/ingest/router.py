"""Ingest endpoint — internal only. Batch + idempotent."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_ingest_key
from app.core.db import get_session
from app.models.reading import Reading
from app.schemas.reading import IngestPayload

router = APIRouter(
    prefix="/api/v1",
    tags=["ingest"],
    dependencies=[Depends(require_ingest_key)],
)


@router.post("/readings", status_code=status.HTTP_202_ACCEPTED)
async def ingest_readings(
    payload: IngestPayload,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Insert readings. Accepts a single reading object (immediate post —
    the normal case at 1/min), a bare JSON list (buffer flush after an
    outage), or {"readings": [...]}. Duplicate `time` values (retries, or
    duplicates within one request) are silently skipped, so the bridge can
    retry safely after a network blip."""
    rows = [
        {
            "time": r.time,
            "pulses": r.pulses,
            "kwh": r.kwh,
            "average_watts": r.average_watts,
        }
        for r in payload.readings
    ]
    stmt = (
        pg_insert(Reading)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[Reading.time])
        .returning(Reading.time)
    )
    result = await session.execute(stmt)
    accepted = len(result.all())
    await session.commit()
    return {"received": len(rows), "accepted": accepted, "duplicates": len(rows) - accepted}
