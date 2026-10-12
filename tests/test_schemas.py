import pytest
from pydantic import ValidationError

from app.schemas.reading import ReadingBatch, ReadingIn


def kwargs(**overrides):
    d = {
        "time": "2026-10-12T06:58:00+10:00",
        "pulses": 12,
        "kwh": 0.012,
        "average_watts": 230.5,
    }
    d.update(overrides)
    return d


def test_valid_reading():
    r = ReadingIn(**kwargs())
    assert r.pulses == 12
    assert r.kwh == 0.012


def test_time_normalised_to_utc():
    r = ReadingIn(**kwargs())
    assert r.time.utcoffset().total_seconds() == 0


def test_missing_field_rejected():
    d = kwargs()
    del d["kwh"]
    with pytest.raises(ValidationError):
        ReadingIn(**d)


def test_naive_time_rejected():
    with pytest.raises(ValidationError):
        ReadingIn(**kwargs(time="2026-10-12T06:58:00"))


def test_negative_pulses_rejected():
    with pytest.raises(ValidationError):
        ReadingIn(**kwargs(pulses=-1))


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        ReadingIn(**kwargs(device="powerpal-1"))


def test_empty_batch_rejected():
    with pytest.raises(ValidationError):
        ReadingBatch(readings=[])
