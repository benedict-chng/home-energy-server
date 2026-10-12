"""Pydantic schemas for the readings API. All fields mandatory per spec."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import accept_single_object_or_list, require_utc_offset


class ReadingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: datetime
    pulses: int = Field(ge=0)
    kwh: float = Field(ge=0)
    average_watts: float = Field(ge=0)

    @field_validator("time")
    @classmethod
    def _require_utc_offset(cls, v: datetime) -> datetime:
        return require_utc_offset(v)


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
    def _normalise_input(cls, data: object) -> object:
        return accept_single_object_or_list(data)


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
