"""Query endpoints — external-facing. Read-only, own API key."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Interval, cast, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_query_key
from app.core.db import get_session
from app.models.reading import Reading
from app.schemas.reading import ReadingsPage, ReadingOut, SummaryPage, SummaryPoint

router = APIRouter(
    prefix="/api/v1",
    tags=["query"],
    dependencies=[Depends(require_query_key)],
)

BUCKETS = {"1m": "1 minute", "5m": "5 minutes", "15m": "15 minutes", "1h": "1 hour", "1d": "1 day"}


@router.get("/readings", response_model=ReadingsPage)
async def list_readings(
    session: AsyncSession = Depends(get_session),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> ReadingsPage:
    """Raw readings in a time range. `from` inclusive, `to` exclusive."""
    if from_ and to and from_ >= to:
        raise HTTPException(status_code=422, detail="'from' must be earlier than 'to'")

    stmt = select(Reading)
    if from_:
        stmt = stmt.where(Reading.time >= from_)
    if to:
        stmt = stmt.where(Reading.time < to)
    stmt = stmt.order_by(Reading.time.desc() if order == "desc" else Reading.time.asc())
    stmt = stmt.offset(offset).limit(limit)

    rows = (await session.execute(stmt)).scalars().all()
    return ReadingsPage(
        count=len(rows),
        readings=[ReadingOut.model_validate(r, from_attributes=True) for r in rows],
    )


@router.get("/readings/latest", response_model=ReadingOut)
async def get_latest_reading(
    session: AsyncSession = Depends(get_session),
) -> ReadingOut:
    """The single most recent reading. No params needed. 404 if DB is empty."""
    row = (
        (await session.execute(select(Reading).order_by(Reading.time.desc()).limit(1)))
        .scalars()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="no readings stored yet")
    return ReadingOut.model_validate(row, from_attributes=True)


@router.get("/readings/summary", response_model=SummaryPage)
async def summarize_readings(
    session: AsyncSession = Depends(get_session),
    bucket: str = Query(default="1h", pattern="^(1m|5m|15m|1h|1d)$"),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
) -> SummaryPage:
    """Time-bucketed aggregates (sum pulses, sum kWh, avg watts).

    Uses TimescaleDB's time_bucket; production DB is Timescale.
    Buckets are UTC.
    """
    if from_ and to and from_ >= to:
        raise HTTPException(status_code=422, detail="'from' must be earlier than 'to'")

    bucket_col = func.time_bucket(cast(literal(BUCKETS[bucket]), Interval()), Reading.time).label(
        "bucket"
    )
    stmt = select(
        bucket_col,
        func.sum(Reading.pulses).label("pulses"),
        func.sum(Reading.kwh).label("kwh"),
        func.avg(Reading.average_watts).label("avg_watts"),
    )
    if from_:
        stmt = stmt.where(Reading.time >= from_)
    if to:
        stmt = stmt.where(Reading.time < to)
    stmt = stmt.group_by(bucket_col).order_by(bucket_col)

    rows = (await session.execute(stmt)).all()
    return SummaryPage(
        bucket=bucket,
        points=[
            SummaryPoint(bucket=r.bucket, pulses=r.pulses, kwh=r.kwh, avg_watts=r.avg_watts)
            for r in rows
        ],
    )
