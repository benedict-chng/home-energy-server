"""Combined grid+solar overview — one call per dashboard superimposition."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Interval, cast, func, join, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_query_key
from app.core.db import get_session
from app.models.reading import Reading
from app.models.solar_reading import SolarReading
from app.query.common import BUCKETS, require_utc_offset, validate_range
from app.schemas.energy import EnergyOverviewPage, EnergyOverviewPoint

router = APIRouter(
    prefix="/api/v1/energy",
    tags=["energy"],
    dependencies=[Depends(require_query_key)],
)


@router.get("/overview", response_model=EnergyOverviewPage)
async def energy_overview(
    session: AsyncSession = Depends(get_session),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    bucket: str = Query(default="1h", pattern="^(1m|5m|15m|1h|1d)$"),
) -> EnergyOverviewPage:
    """Grid consumption vs solar generation, time-aligned in one response.

    Two time_bucket aggregations FULL OUTER JOINed on bucket, so buckets
    with only one side present still appear (the other side gets 0 kWh and
    a null avg). Buckets are UTC. Ideal for superimposing the two curves.
    """
    validate_range(from_, to)
    from_ = require_utc_offset("from", from_)
    to = require_utc_offset("to", to)
    interval = BUCKETS[bucket]

    def aggregates(model, energy_col, watts_col, energy_label: str, watts_label: str):
        b = func.time_bucket(cast(literal(interval), Interval()), model.time)
        q = select(
            b.label("bucket"),
            func.sum(energy_col).label(energy_label),
            func.avg(watts_col).label(watts_label),
        )
        if from_:
            q = q.where(model.time >= from_)
        if to:
            q = q.where(model.time < to)
        return q.group_by(b).subquery()

    grid = aggregates(
        Reading, Reading.kwh, Reading.average_watts, "consumed_kwh", "avg_grid_watts"
    )
    solar = aggregates(
        SolarReading,
        SolarReading.energy_kwh,
        SolarReading.power_watts,
        "generated_kwh",
        "avg_solar_watts",
    )

    bucket_col = func.coalesce(grid.c.bucket, solar.c.bucket)
    stmt = (
        select(
            bucket_col.label("bucket"),
            func.coalesce(grid.c.consumed_kwh, 0.0).label("consumed_kwh"),
            func.coalesce(solar.c.generated_kwh, 0.0).label("generated_kwh"),
            grid.c.avg_grid_watts,
            solar.c.avg_solar_watts,
        )
        .select_from(join(grid, solar, grid.c.bucket == solar.c.bucket, full=True))
        .order_by(bucket_col)
    )

    rows = (await session.execute(stmt)).all()
    return EnergyOverviewPage(
        bucket=bucket,
        points=[
            EnergyOverviewPoint(
                bucket=r.bucket,
                consumed_kwh=r.consumed_kwh,
                generated_kwh=r.generated_kwh,
                avg_grid_watts=r.avg_grid_watts,
                avg_solar_watts=r.avg_solar_watts,
            )
            for r in rows
        ],
    )
