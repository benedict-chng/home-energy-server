"""Combined grid+solar overview schemas — one call per dashboard superimposition."""

from datetime import datetime

from pydantic import BaseModel


class EnergyOverviewPoint(BaseModel):
    bucket: datetime
    consumed_kwh: float
    generated_kwh: float
    avg_grid_watts: float | None
    avg_solar_watts: float | None


class EnergyOverviewPage(BaseModel):
    bucket: str
    points: list[EnergyOverviewPoint]
