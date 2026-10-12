"""Ingest endpoint — internal only. Batch + idempotent."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_ingest_key
from app.core.db import get_session
from app.models.reading import Reading
from app.schemas.reading import ReadingBatch

router = APIRouter(
    prefix="/api/v1",
    tags=["ingest"],
    dependencies=[Depends(require_ingest_key)],
)


@router.post("/readings", status_code=status.HTTP_202_ACCEPTED)
async def ingest_readings(
    batch: ReadingBatch,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Insert a batch of readings. Duplicate `time` values (retries, or
    duplicates within the batch) are silently skipped, so the bridge can
    retry safely after a network blip."""
    rows = [
        {
            "time": r.time,
            "pulses": r.pulses,
            "kwh": r.kwh,
            "average_watts": r.average_watts,
        }
        for r in batch.readings
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
