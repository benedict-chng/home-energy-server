"""Solar query endpoints — external-facing. Read-only, query API key."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Interval, cast, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_query_key
from app.core.db import get_session
from app.models.solar_reading import SolarReading
from app.query.common import BUCKETS, require_utc_offset, validate_range
from app.schemas.solar import SolarPage, SolarReadingOut, SolarSummaryPage, SolarSummaryPoint

router = APIRouter(
    prefix="/api/v1/solar",
    tags=["solar query"],
    dependencies=[Depends(require_query_key)],
)


@router.get("/readings", response_model=SolarPage)
async def list_solar_readings(
    session: AsyncSession = Depends(get_session),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> SolarPage:
    """Raw solar readings in a time range. `from` inclusive, `to` exclusive.
    Both ISO 8601 with UTC offset (e.g. 2026-10-12T00:00:00+11:00 or ...Z)."""
    from_ = require_utc_offset("from", from_)
    to = require_utc_offset("to", to)
    validate_range(from_, to)

    stmt = select(SolarReading)
    if from_:
        stmt = stmt.where(SolarReading.time >= from_)
    if to:
        stmt = stmt.where(SolarReading.time < to)
    stmt = stmt.order_by(SolarReading.time.desc() if order == "desc" else SolarReading.time.asc())
    stmt = stmt.offset(offset).limit(limit)

    rows = (await session.execute(stmt)).scalars().all()
    return SolarPage(
        count=len(rows),
        readings=[SolarReadingOut.model_validate(r, from_attributes=True) for r in rows],
    )


@router.get("/readings/latest", response_model=SolarReadingOut)
async def get_latest_solar_reading(
    session: AsyncSession = Depends(get_session),
) -> SolarReadingOut:
    """The single most recent solar reading. No params needed. 404 if empty."""
    row = (
        (
            await session.execute(
                select(SolarReading).order_by(SolarReading.time.desc()).limit(1)
            )
        )
        .scalars()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="no solar readings stored yet")
    return SolarReadingOut.model_validate(row, from_attributes=True)


@router.get("/readings/summary", response_model=SolarSummaryPage)
async def summarize_solar_readings(
    session: AsyncSession = Depends(get_session),
    bucket: str = Query(default="1h", pattern="^(1m|5m|15m|1h|1d)$"),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
) -> SolarSummaryPage:
    """Time-bucketed solar aggregates (sum kWh, avg watts). Timescale
    time_bucket; buckets are UTC."""
    validate_range(from_, to)
    from_ = require_utc_offset("from", from_)
    to = require_utc_offset("to", to)
    bucket_col = func.time_bucket(
        cast(literal(BUCKETS[bucket]), Interval()), SolarReading.time
    ).label("bucket")
    stmt = select(
        bucket_col,
        func.avg(SolarReading.average_watts).label("avg_watts"),
    )
    if from_:
        stmt = stmt.where(SolarReading.time >= from_)
    if to:
        stmt = stmt.where(SolarReading.time < to)
    stmt = stmt.group_by(bucket_col).order_by(bucket_col)

    rows = (await session.execute(stmt)).all()
    return SolarSummaryPage(
        bucket=bucket,
        points=[
            SolarSummaryPoint(bucket=r.bucket, energy_kwh=r.energy_kwh, avg_watts=r.avg_watts)
            for r in rows
        ],
    )
