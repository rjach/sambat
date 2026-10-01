from __future__ import annotations

import datetime as dt

import pytest

from sambat import NEPAL_TZ, date, datetime


@pytest.mark.parametrize(
    "text",
    ["2083-06-15", "20830615", "2083-W25-4", "2083W254", "2083-W25", "2083W25"],
)
def test_date_forms(text: str) -> None:
    expected = date(2083, 6, 12) if text in {"2083-W25", "2083W25"} else date(2083, 6, 15)
    assert date.fromisoformat(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2083-06-15T09:30", datetime(2083, 6, 15, 9, 30)),
        ("2083-06-15 09:30:05", datetime(2083, 6, 15, 9, 30, 5)),
        ("2083-06-15T09:30:05.123", datetime(2083, 6, 15, 9, 30, 5, 123000)),
        ("2083-06-15T09:30:05,5", datetime(2083, 6, 15, 9, 30, 5, 500000)),
        ("20830615T0930", datetime(2083, 6, 15, 9, 30)),
        ("2083-06-15T09", datetime(2083, 6, 15, 9)),
        ("2083-06-15", datetime(2083, 6, 15)),
        ("2083-W25-4T09:30", datetime(2083, 6, 15, 9, 30)),
        ("2083W254T09", datetime(2083, 6, 15, 9)),
        ("2083W25T09", datetime(2083, 6, 12, 9)),
        ("2083-W25T09", datetime(2083, 6, 12, 9)),
        ("2083-W25-0930", datetime(2083, 6, 12, 9, 30)),
        ("2083-06-15T09:30+05:45", datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ)),
        ("2083-06-15T04:00Z", datetime(2083, 6, 15, 4, tzinfo=dt.UTC)),
    ],
)
def test_datetime_forms(text: str, expected: datetime) -> None:
    value = datetime.fromisoformat(text)
    assert value == expected
    assert value.utcoffset() == expected.utcoffset()


def test_round_trip() -> None:
    value = datetime(2083, 6, 15, 9, 30, 5, 123456, tzinfo=NEPAL_TZ)
    assert datetime.fromisoformat(value.isoformat()) == value
    assert date.fromisoformat(value.date().isoformat()) == value.date()


@pytest.mark.parametrize(
    "text",
    [
        "",
        "2083",
        "2083-6-15",
        "2083/06/15",
        "2083-0615",
        "208306-15",
        "2083-06-15T",
        "2083-06-15T25:00",
        "2083-W54-1",
        "2083-W00-1",
        "2083-W25-8",
        "2083-W254",
        "2083W25-4",
        "२०८३-०६-१५",
        "2083-04-32",
        "2084-01-01",
    ],
)
def test_invalid(text: str) -> None:
    with pytest.raises(ValueError, match="Invalid isoformat string"):
        datetime.fromisoformat(text)


def test_date_rejects_time_component() -> None:
    with pytest.raises(ValueError, match="Invalid isoformat string"):
        date.fromisoformat("2083-06-15T09:30")


def test_type_errors() -> None:
    with pytest.raises(TypeError):
        date.fromisoformat(20830615)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        datetime.fromisoformat(b"2083-06-15")  # type: ignore[arg-type]
