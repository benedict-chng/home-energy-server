"""Solar (Fronius) reading schemas. Two fields only (Ben, 18:28): time +
average_watts, both mandatory. Same contract as grid: values >= 0, unknown
fields rejected, naive timestamps rejected."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import accept_single_object_or_list, require_utc_offset


class SolarReadingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: datetime
    average_watts: float = Field(ge=0)

    @field_validator("time")
    @classmethod
    def _require_utc_offset(cls, v: datetime) -> datetime:
        return require_utc_offset(v)


class SolarPayload(BaseModel):
    """Accepts a single reading object (immediate post), a bare JSON list
    (buffer flush), or the wrapped {"readings": [...]} form."""

    model_config = ConfigDict(extra="forbid")

    readings: list[SolarReadingIn] = Field(min_length=1, max_length=1000)

    @model_validator(mode="before")
    @classmethod
    def _normalise_input(cls, data: object) -> object:
        return accept_single_object_or_list(data)


class SolarReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    average_watts: float


class SolarPage(BaseModel):
    count: int
    readings: list[SolarReadingOut]


class SolarSummaryPoint(BaseModel):
    bucket: datetime
    avg_watts: float


class SolarSummaryPage(BaseModel):
    bucket: str
    points: list[SolarSummaryPoint]
