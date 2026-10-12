"""Solar (Fronius) ingest — internal only. Same contract as grid ingest."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_ingest_key
from app.core.db import get_session
from app.ingest.common import insert_idempotent
from app.models.solar_reading import SolarReading
from app.schemas.solar import SolarPayload

router = APIRouter(
    prefix="/api/v1/solar",
    tags=["solar ingest"],
    dependencies=[Depends(require_ingest_key)],
)


@router.post("/readings", status_code=status.HTTP_202_ACCEPTED)
async def ingest_solar_readings(
    payload: SolarPayload,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Insert solar readings. Same rules as grid: accepts a single object
    (immediate post), a bare list (buffer flush), or {"readings": [...]};
    duplicate `time` values are silently skipped so the bridge can retry
    safely. Existing grid endpoints are untouched — this is additive."""
    rows = [
        {"time": r.time, "power_watts": r.power_watts, "energy_kwh": r.energy_kwh}
        for r in payload.readings
    ]
    return await insert_idempotent(session, SolarReading, rows)
