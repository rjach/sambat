from __future__ import annotations

import datetime as dt

import pytest

from sambat import NEPAL_TZ, date, datetime
from sambat.locale import NE


@pytest.mark.parametrize(
    ("text", "fmt", "expected"),
    [
        ("2083-06-15", "%Y-%m-%d", date(2083, 6, 15)),
        ("15 Ashwin 2083", "%d %B %Y", date(2083, 6, 15)),
        ("15 asoj 2083", "%d %B %Y", date(2083, 6, 15)),
        ("15 ASH 2083", "%d %b %Y", date(2083, 6, 15)),
        ("Thursday 15 Ashwin 2083", "%A %d %B %Y", date(2083, 6, 15)),
        ("06/15/83", "%D", date(2083, 6, 15)),
        ("2083-171", "%Y-%j", date(2083, 6, 15)),
        ("2083 24 4", "%Y %U %w", date(2083, 6, 15)),
        ("2083 24 Thu", "%Y %W %a", date(2083, 6, 15)),
        ("2083-W25-4", "%G-W%V-%u", date(2083, 6, 15)),
        ("२०८३-०६-१५", "%Y-%m-%d", date(2083, 6, 15)),
        ("२०८३-०६-१५", "%OY-%Om-%Od", date(2083, 6, 15)),
        ("2083 3 32", "%Y %m %d", date(2083, 3, 32)),
        ("2083%15", "%Y%%%d", date(2083, 1, 15)),
    ],
)
def test_date_strptime(text: str, fmt: str, expected: date) -> None:
    assert date.strptime(text, fmt) == expected


def test_nepali_names() -> None:
    assert date.strptime("२०८३ असोज १५", "%Y %B %d", locale=NE) == date(2083, 6, 15)
    assert date.strptime("२०८३ आश्विन १५", "%Y %B %d", locale=NE) == date(2083, 6, 15)
    assert date.strptime("बिहिबार, २०८३ असोज १५", "%A, %Y %B %d", locale=NE) == date(2083, 6, 15)


def test_datetime_strptime() -> None:
    value = datetime.strptime("2083-06-15 02:05:09.25 PM +0545", "%Y-%m-%d %I:%M:%S.%f %p %z")
    assert value == datetime(2083, 6, 15, 14, 5, 9, 250000, tzinfo=NEPAL_TZ)
    assert value.utcoffset() == dt.timedelta(hours=5, minutes=45)
    assert datetime.strptime("12 AM", "%I %p").hour == 0
    assert datetime.strptime("2083 12:00 AM", "%Y %I:%M %p").hour == 0


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        ("Z", dt.timedelta(0)),
        ("+05:45", dt.timedelta(hours=5, minutes=45)),
        ("-0330", -dt.timedelta(hours=3, minutes=30)),
        ("+05:41:16", dt.timedelta(hours=5, minutes=41, seconds=16)),
        ("+05:41:16.5", dt.timedelta(hours=5, minutes=41, seconds=16, microseconds=500000)),
    ],
)
def test_offsets(offset: str, expected: dt.timedelta) -> None:
    value = datetime.strptime(f"2083-01-01 {offset}", "%Y-%m-%d %z")
    assert value.utcoffset() == expected


def test_tzname_with_offset() -> None:
    value = datetime.strptime("2083-01-01 +0545 NPT", "%Y-%m-%d %z %Z")
    assert value.tzname() == "NPT"
    naive = datetime.strptime("2083-01-01 UTC", "%Y-%m-%d %Z")
    assert naive.tzinfo is None


def test_round_trip_with_composites() -> None:
    value = datetime(2083, 6, 15, 14, 5, 9)
    for fmt in ("%c", "%x %X", "%F %T", "%D %r"):
        assert datetime.strptime(value.strftime(fmt), fmt).replace(second=9) == value


def test_two_digit_year_is_in_twenty_first_century() -> None:
    assert date.strptime("83-01-01", "%y-%m-%d") == date(2083, 1, 1)


def test_missing_year_defaults_to_2000_and_warns() -> None:
    with pytest.warns(DeprecationWarning, match="without a year"):
        assert date.strptime("15 Asoj", "%d %B") == date(2000, 6, 15)
    assert date.strptime("Asoj", "%B") == date(2000, 6, 1)


@pytest.mark.parametrize(
    ("text", "fmt", "message"),
    [
        ("2083-06", "%Y-%m-%d", "does not match"),
        ("2083-06-15x", "%Y-%m-%d", "unconverted data remains"),
        ("2083-04-32", "%Y-%m-%d", "day must be"),
        ("2083-13-01", "%Y-%m-%d", "month must be"),
        ("2083-367", "%Y-%j", "day of year"),
        ("2083", "%Y %Q", "invalid format directive"),
        ("2083", "%Y%", "stray %"),
        ("2083 2083", "%Y %Y", "redefinition"),
        ("2083-W25", "%G-W%V", "requires"),
    ],
)
def test_errors(text: str, fmt: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        date.strptime(text, fmt)


def test_argument_types() -> None:
    with pytest.raises(TypeError, match="date_string"):
        date.strptime(b"2083", "%Y")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="format"):
        date.strptime("2083", b"%Y")  # type: ignore[arg-type]
