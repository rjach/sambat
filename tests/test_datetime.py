from __future__ import annotations

import copy
import datetime as dt
import pickle
from zoneinfo import ZoneInfo

import pytest

import sambat
from sambat import NEPAL_TZ, date, datetime

NEW_YORK = ZoneInfo("America/New_York")


def test_construction_and_fields() -> None:
    value = datetime(2083, 6, 15, 9, 30, 15, 250, tzinfo=NEPAL_TZ, fold=1)
    assert (value.year, value.month, value.day) == (2083, 6, 15)
    assert (value.hour, value.minute, value.second, value.microsecond) == (9, 30, 15, 250)
    assert value.tzinfo is NEPAL_TZ
    assert value.fold == 1
    assert isinstance(value, date)


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"hour": 24}, ValueError),
        ({"minute": 60}, ValueError),
        ({"second": 60}, ValueError),
        ({"microsecond": 1_000_000}, ValueError),
        ({"fold": 2}, ValueError),
        ({"tzinfo": "UTC"}, TypeError),
        ({"hour": 1.5}, TypeError),
    ],
)
def test_invalid_time_fields(kwargs: dict[str, object], error: type[Exception]) -> None:
    with pytest.raises(error):
        datetime(2083, 1, 1, **kwargs)  # type: ignore[arg-type]


def test_class_attributes() -> None:
    assert datetime.min == datetime(sambat.MINYEAR, 1, 1)
    assert datetime.max.date() == date.max
    assert datetime.max.time() == dt.time(23, 59, 59, 999_999)
    assert datetime.resolution == dt.timedelta(microseconds=1)


def test_repr() -> None:
    assert repr(datetime(2083, 6, 15)) == "sambat.datetime(2083, 6, 15, 0, 0)"
    assert repr(datetime(2083, 6, 15, 1, 2, 3)) == "sambat.datetime(2083, 6, 15, 1, 2, 3)"
    assert repr(datetime(2083, 6, 15, 1, 2, 0, 5)) == "sambat.datetime(2083, 6, 15, 1, 2, 0, 5)"
    aware = datetime(2083, 6, 15, 1, tzinfo=NEPAL_TZ, fold=1)
    assert repr(aware) == "sambat.datetime(2083, 6, 15, 1, 0, tzinfo=sambat.NEPAL_TZ, fold=1)"


def test_gregorian_twin() -> None:
    value = datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ)
    assert value.to_gregorian() == dt.datetime(2026, 10, 1, 9, 30, tzinfo=NEPAL_TZ)
    assert datetime.from_gregorian(value.to_gregorian()) == value
    assert datetime.from_gregorian(dt.date(2026, 10, 1)) == datetime(2083, 6, 15)


def test_now_and_today() -> None:
    before = dt.datetime.now(dt.UTC)
    now = datetime.now(dt.UTC)
    after = dt.datetime.now(dt.UTC)
    assert before <= now.to_gregorian() <= after
    assert datetime.now().tzinfo is None
    assert datetime.today().tzinfo is None


def test_nepal_helpers() -> None:
    now = sambat.now_np()
    assert now.tzinfo is NEPAL_TZ
    assert sambat.today_np() in {now.date(), (now + dt.timedelta(seconds=5)).date()}


def test_fromtimestamp_and_timestamp() -> None:
    stamp = 1_790_826_300.5
    aware = datetime.fromtimestamp(stamp, NEPAL_TZ)
    assert aware.isoformat() == "2083-06-15T09:30:00.500000+05:45"
    assert aware.timestamp() == stamp
    naive = datetime.fromtimestamp(stamp)
    assert naive.to_gregorian() == dt.datetime.fromtimestamp(stamp)


def test_deprecated_utc_constructors() -> None:
    with pytest.warns(DeprecationWarning, match="utcnow"):
        value = datetime.utcnow()
    assert value.tzinfo is None
    with pytest.warns(DeprecationWarning, match="utcfromtimestamp"):
        value = datetime.utcfromtimestamp(0)
    assert value.to_gregorian() == dt.datetime(1970, 1, 1)


def test_combine() -> None:
    clock = dt.time(9, 30, tzinfo=NEPAL_TZ, fold=1)
    value = datetime.combine(date(2083, 6, 15), clock)
    assert value == datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ, fold=1)
    assert datetime.combine(date(2083, 6, 15), clock, tzinfo=None).tzinfo is None
    with pytest.raises(TypeError, match=r"sambat\.date"):
        datetime.combine(dt.date(2026, 10, 1), clock)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"datetime\.time"):
        datetime.combine(date(2083, 6, 15), "09:30")  # type: ignore[arg-type]


def test_date_time_timetz() -> None:
    value = datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ, fold=1)
    assert value.date() == date(2083, 6, 15)
    assert type(value.date()) is date
    assert value.time() == dt.time(9, 30, fold=1)
    assert value.timetz() == dt.time(9, 30, tzinfo=NEPAL_TZ, fold=1)


def test_timezone_queries() -> None:
    aware = datetime(2083, 6, 15, 9, 30, tzinfo=NEW_YORK)
    assert aware.utcoffset() == dt.timedelta(hours=-4)
    assert aware.dst() == dt.timedelta(hours=1)
    assert aware.tzname() == "EDT"
    naive = datetime(2083, 6, 15)
    assert naive.utcoffset() is None
    assert naive.dst() is None
    assert naive.tzname() is None


def test_astimezone() -> None:
    value = datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ)
    utc = value.astimezone(dt.UTC)
    assert utc == value
    assert (utc.hour, utc.minute) == (3, 45)
    assert utc.astimezone(NEPAL_TZ).hour == 9
    assert value.astimezone().tzinfo is not None


def test_timetuple_and_utctimetuple() -> None:
    value = datetime(2083, 6, 15, 1, 0, tzinfo=NEPAL_TZ)
    assert tuple(value.timetuple()) == (2083, 6, 15, 1, 0, 0, 3, 171, 0)
    assert tuple(value.utctimetuple()) == (2083, 6, 14, 19, 15, 0, 2, 170, 0)
    assert value.replace(tzinfo=None).timetuple().tm_isdst == -1
    assert datetime(2083, 6, 15, tzinfo=NEW_YORK).timetuple().tm_isdst == 1


def test_isoformat_timespecs() -> None:
    value = datetime(2083, 6, 15, 9, 30, 5, 123456, tzinfo=NEPAL_TZ)
    assert value.isoformat() == "2083-06-15T09:30:05.123456+05:45"
    assert value.isoformat(" ", "minutes") == "2083-06-15 09:30+05:45"
    assert value.isoformat(timespec="milliseconds") == "2083-06-15T09:30:05.123+05:45"
    assert str(value) == "2083-06-15 09:30:05.123456+05:45"
    with pytest.raises(ValueError, match="timespec"):
        value.isoformat(timespec="days")


def test_ctime_and_strftime() -> None:
    value = datetime(2083, 6, 15, 14, 5, 9)
    assert value.ctime() == "Thu Ash 15 14:05:09 2083"
    assert value.strftime("%I:%M %p") == "02:05 PM"


def test_replace() -> None:
    value = datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ)
    assert value.replace(hour=10).hour == 10
    assert value.replace(tzinfo=None).tzinfo is None
    assert value.replace(fold=1).fold == 1
    assert value.replace().tzinfo is NEPAL_TZ
    assert value.__replace__(minute=0).minute == 0


def test_comparisons_naive_and_aware() -> None:
    a = datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ)
    b = datetime(2083, 6, 15, 3, 45, tzinfo=dt.UTC)
    assert a == b
    assert hash(a) == hash(b)
    assert a <= b <= a
    naive = datetime(2083, 6, 15, 9, 30)
    assert naive != a
    with pytest.raises(TypeError):
        _ = naive < a
    assert naive > datetime(2083, 6, 15)
    assert datetime(2083, 6, 15) < naive
    assert naive >= datetime(2083, 6, 15, 9, 30)


def test_no_comparison_with_stdlib_datetime() -> None:
    value = datetime(2083, 6, 15)
    assert value != value.to_gregorian()
    with pytest.raises(TypeError):
        _ = value < value.to_gregorian()  # type: ignore[operator]


def test_arithmetic() -> None:
    value = datetime(2083, 3, 32, 23, 0, tzinfo=NEPAL_TZ)
    assert value + dt.timedelta(hours=2) == datetime(2083, 4, 1, 1, 0, tzinfo=NEPAL_TZ)
    assert dt.timedelta(hours=2) + value == value + dt.timedelta(hours=2)
    assert value - dt.timedelta(days=1) == datetime(2083, 3, 31, 23, tzinfo=NEPAL_TZ)
    other = datetime(2083, 3, 32, 17, 15, tzinfo=dt.UTC)
    assert value - other == dt.timedelta(0)
    with pytest.raises(TypeError):
        _ = value - datetime(2083, 1, 1)
    with pytest.raises(TypeError):
        _ = value + 1  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = value - 1


def test_arithmetic_overflow() -> None:
    with pytest.raises(OverflowError):
        datetime.max + dt.timedelta(microseconds=1)
    with pytest.raises(OverflowError):
        datetime.min - dt.timedelta(microseconds=1)
    with pytest.raises(OverflowError):
        datetime.min + dt.timedelta.max


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_roundtrip(protocol: int) -> None:
    for value in (
        datetime(2083, 6, 15, 9, 30, 1, 2),
        datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ, fold=1),
        datetime(2083, 6, 15, 9, 30, tzinfo=dt.timezone(dt.timedelta(hours=3))),
    ):
        restored = pickle.loads(pickle.dumps(value, protocol))
        assert restored == value
        assert restored.fold == value.fold
        assert restored.tzinfo == value.tzinfo


def test_copy() -> None:
    value = datetime(2083, 6, 15, 9, tzinfo=NEPAL_TZ, fold=1)
    assert copy.copy(value).fold == 1
    assert copy.deepcopy(value) == value


class MyDateTime(datetime):
    __slots__ = ()


def test_subclass_preserved() -> None:
    value = MyDateTime(2083, 6, 15, 9, tzinfo=NEPAL_TZ)
    assert type(value + dt.timedelta(hours=1)) is MyDateTime
    assert type(value.replace(hour=1)) is MyDateTime
    assert type(value.astimezone(dt.UTC)) is MyDateTime
    assert type(MyDateTime.now()) is MyDateTime
    assert type(MyDateTime.fromisoformat("2083-06-15T09:00")) is MyDateTime
    assert type(value.date()) is date
