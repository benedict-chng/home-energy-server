import pytest
from pydantic import ValidationError

from app.schemas.solar import SolarPayload, SolarReadingIn


def kwargs(**overrides):
    d = {
        "time": "2026-10-12T12:00:00+10:00",
        "power_watts": 2450.5,
        "energy_kwh": 0.24,
    }
    d.update(overrides)
    return d


def test_valid_reading():
    r = SolarReadingIn(**kwargs())
    assert r.power_watts == 2450.5


def test_time_normalised_to_utc():
    r = SolarReadingIn(**kwargs())
    assert r.time.utcoffset().total_seconds() == 0


def test_missing_field_rejected():
    d = kwargs()
    del d["energy_kwh"]
    with pytest.raises(ValidationError):
        SolarReadingIn(**d)


def test_naive_time_rejected():
    with pytest.raises(ValidationError):
        SolarReadingIn(**kwargs(time="2026-10-12T12:00:00"))


def test_negative_power_rejected():
    with pytest.raises(ValidationError):
        SolarReadingIn(**kwargs(power_watts=-1))


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        SolarReadingIn(**kwargs(inverter="fronius"))


def test_single_object_accepted():
    # Immediate post — the normal case
    p = SolarPayload(**kwargs())
    assert len(p.readings) == 1


def test_bare_list_accepted():
    p = SolarPayload.model_validate([kwargs(), kwargs()])
    assert len(p.readings) == 2


def test_wrapped_form_accepted():
    p = SolarPayload(readings=[kwargs()])
    assert len(p.readings) == 1


def test_empty_list_rejected():
    with pytest.raises(ValidationError):
        SolarPayload.model_validate([])
