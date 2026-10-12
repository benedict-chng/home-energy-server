"""Pydantic schemas for the readings API. All fields mandatory per spec."""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReadingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: datetime
    pulses: int = Field(ge=0)
    kwh: float = Field(ge=0)
    average_watts: float = Field(ge=0)

    @field_validator("time")
    @classmethod
    def _require_utc_offset(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError(
                "time must be ISO 8601 with a UTC offset, e.g. 2026-10-12T06:58:00+10:00"
            )
        return v.astimezone(timezone.utc)


class ReadingBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    readings: list[ReadingIn] = Field(min_length=1, max_length=1000)


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    pulses: int
    kwh: float
    average_watts: float


class ReadingsPage(BaseModel):
    count: int
    readings: list[ReadingOut]


class SummaryPoint(BaseModel):
    bucket: datetime
    pulses: float
    kwh: float
    avg_watts: float


class SummaryPage(BaseModel):
    bucket: str
    points: list[SummaryPoint]
