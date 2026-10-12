"""PowerPal reading, as specified by Ben on 2026-10-12.

All four fields mandatory. `time` is the primary key so bridge retries are
idempotent (ON CONFLICT DO NOTHING). Stored as UTC timestamptz.
"""

from datetime import datetime

from sqlalchemy import DateTime, Double, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Reading(Base):
    __tablename__ = "readings"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    pulses: Mapped[int] = mapped_column(Integer, nullable=False)
    kwh: Mapped[float] = mapped_column(Double, nullable=False)
    average_watts: Mapped[float] = mapped_column(Double, nullable=False)
