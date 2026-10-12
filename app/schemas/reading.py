"""Pydantic schemas for the readings API. All fields mandatory per spec."""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class IngestPayload(BaseModel):
    """Body for POST /api/v1/readings. Accepts any of:

    - a single reading object  — immediate post, the normal case (1/min)
    - a bare JSON list         — e.g. bridge flushing its buffer after an outage
    - {"readings": [...]}      — wrapped form

    All shapes normalise to the same validated list; extra="forbid" still
    applies to each reading object via ReadingIn.
    """

    model_config = ConfigDict(extra="forbid")

    readings: list[ReadingIn] = Field(min_length=1, max_length=1000)

    @model_validator(mode="before")
    @classmethod
    def _accept_single_object_or_list(cls, data: object) -> object:
        if isinstance(data, dict) and "readings" not in data:
            return {"readings": [data]}
        if isinstance(data, list):
            return {"readings": data}
        return data


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
