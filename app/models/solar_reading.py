"""Solar (Fronius) reading, mirroring the grid `Reading` pattern.

Two fields only (Ben, 18:28): `time` + `average_watts`. All mandatory.
`time` is the primary key so bridge retries are idempotent (ON CONFLICT
DO NOTHING). Stored as UTC timestamptz.
"""

from datetime import datetime

from sqlalchemy import DateTime, Double
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SolarReading(Base):
    __tablename__ = "solar_readings"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    average_watts: Mapped[float] = mapped_column(Double, nullable=False)
