from __future__ import annotations

import copy
import datetime as dt
import pickle
from decimal import Decimal

import pytest

import sambat
from sambat import MAXYEAR, MINYEAR, date

# Dates whose Gregorian equivalent is known independently of any calendar table.
HISTORICAL = [
    ((2007, 11, 7), dt.date(1951, 2, 18)),  # Democracy Day (Falgun 7, 2007)
    ((2046, 12, 26), dt.date(1990, 4, 8)),  # multiparty democracy restored
    ((2047, 7, 23), dt.date(1990, 11, 9)),  # 1990 constitution promulgated
    ((2063, 1, 11), dt.date(2006, 4, 24)),  # parliament reinstated (Loktantra Diwas)
    ((2065, 2, 15), dt.date(2008, 5, 28)),  # republic declared
    ((2072, 1, 12), dt.date(2015, 4, 25)),  # Gorkha earthquake
    ((2072, 6, 3), dt.date(2015, 9, 20)),  # constitution promulgated
    ((2081, 1, 1), dt.date(2024, 4, 13)),  # New Year 2081
    ((2082, 1, 1), dt.date(2025, 4, 14)),  # official panchang 2082
    ((2083, 1, 1), dt.date(2026, 4, 14)),  # official panchang 2083
    ((2083, 7, 1), dt.date(2026, 10, 18)),  # official panchang 2083 (Kartik 1)
]


@pytest.mark.parametrize(("bs", "ad"), HISTORICAL)
def test_known_conversions(bs: tuple[int, int, int], ad: dt.date) -> None:
    value = date(*bs)
    assert value.to_gregorian() == ad
    assert date.from_gregorian(ad) == value
    assert value.toordinal() == ad.toordinal()
    assert value.weekday() == ad.weekday()


def test_fields_and_repr() -> None:
    value = date(2083, 6, 15)
    assert (value.year, value.month, value.day) == (2083, 6, 15)
    assert repr(value) == "sambat.date(2083, 6, 15)"
    assert str(value) == value.isoformat() == "2083-06-15"
    assert type(value).__module__ == "sambat"


def test_class_attributes() -> None:
    assert date.min == date(MINYEAR, 1, 1)
    assert date.max.year == MAXYEAR
    assert date.max.month == 12
    assert date.resolution == dt.timedelta(days=1)
    assert (date.max + dt.timedelta(0)) == date.max


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ((MAXYEAR + 1, 1, 1), "out of range"),
        ((MINYEAR - 1, 1, 1), "out of range"),
        ((2083, 0, 1), "month must be in 1..12"),
        ((2083, 13, 1), "month must be in 1..12"),
        ((2083, 1, 0), "day must be in 1..31"),
        ((2083, 3, 33), "day must be in 1..32"),
        ((2083, 4, 32), "day must be in 1..31"),
    ],
)
def test_invalid_fields(args: tuple[int, int, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        date(*args)


def test_out_of_range_message_explains_why() -> None:
    with pytest.raises(ValueError, match="officially published"):
        date(MAXYEAR + 1, 1, 1)


@pytest.mark.parametrize("bad", [1.0, "1", Decimal(1), None])
def test_non_integer_arguments(bad: object) -> None:
    with pytest.raises(TypeError):
        date(2083, bad, 1)  # type: ignore[arg-type]


def test_index_protocol_and_bool_accepted() -> None:
    class Index:
        def __index__(self) -> int:
            return 6

    assert date(2083, Index(), True) == date(2083, 6, 1)  # type: ignore[arg-type]


def test_day_32_exists_in_long_months() -> None:
    assert date(2083, 3, 32).days_in_month() == 32
    assert date(2081, 1, 1).days_in_year() == 366


def test_today_matches_stdlib() -> None:
    before = dt.date.today()
    today = date.today()
    after = dt.date.today()
    assert today.to_gregorian() in {before, after}


def test_fromtimestamp_matches_stdlib() -> None:
    stamp = 1_790_826_300.0
    assert date.fromtimestamp(stamp).to_gregorian() == dt.date.fromtimestamp(stamp)


def test_fromordinal_bounds() -> None:
    assert date.fromordinal(date.min.toordinal()) == date.min
    assert date.fromordinal(date.max.toordinal()) == date.max
    with pytest.raises(ValueError, match="out of range"):
        date.fromordinal(date.min.toordinal() - 1)
    with pytest.raises(ValueError, match="out of range"):
        date.fromordinal(date.max.toordinal() + 1)


def test_weekday_isoweekday() -> None:
    value = date(2083, 6, 15)  # Thursday 2026-10-01
    assert value.weekday() == 3
    assert value.isoweekday() == 4


def test_timetuple() -> None:
    value = date(2083, 6, 15)
    parts = value.timetuple()
    assert tuple(parts) == (2083, 6, 15, 0, 0, 0, 3, 171, -1)


def test_ctime() -> None:
    assert date(2083, 6, 5).ctime() == "Mon Ash  5 00:00:00 2083"


def test_replace() -> None:
    value = date(2083, 6, 15)
    assert value.replace(day=1) == date(2083, 6, 1)
    assert value.replace(year=2080, month=1) == date(2080, 1, 15)
    assert value.__replace__(month=7) == date(2083, 7, 15)
    with pytest.raises(ValueError, match="day must be"):
        date(2083, 3, 32).replace(month=4)


def test_comparisons() -> None:
    a, b = date(2083, 1, 1), date(2083, 1, 2)
    assert a < b <= date(2083, 1, 2)
    assert b > a >= date(2083, 1, 1)
    assert a != b
    assert a == date(2083, 1, 1)


def test_no_cross_calendar_comparison() -> None:
    bs = date(2083, 1, 1)
    ad = bs.to_gregorian()
    assert bs != ad
    assert ad != bs
    with pytest.raises(TypeError):
        _ = bs < ad  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = bs - ad  # type: ignore[operator]


def test_date_and_datetime_are_not_comparable() -> None:
    d = date(2083, 1, 1)
    t = sambat.datetime(2083, 1, 1)
    assert d != t
    assert t != d
    with pytest.raises(TypeError):
        _ = d < t
    with pytest.raises(TypeError):
        _ = d - t  # type: ignore[operator]


def test_hash_matches_gregorian_and_is_stable() -> None:
    value = date(2083, 6, 15)
    assert hash(value) == hash(value.to_gregorian())
    assert hash(value) == hash(date(2083, 6, 15))
    assert {value, date(2083, 6, 15)} == {value}


def test_arithmetic() -> None:
    value = date(2083, 3, 32)
    assert value + dt.timedelta(days=1) == date(2083, 4, 1)
    assert dt.timedelta(days=1) + value == date(2083, 4, 1)
    assert value - dt.timedelta(days=32) == date(2083, 2, 31)
    assert date(2083, 4, 1) - value == dt.timedelta(days=1)
    assert value + dt.timedelta(hours=23) == value


def test_arithmetic_overflow() -> None:
    with pytest.raises(OverflowError):
        date.max + dt.timedelta(days=1)
    with pytest.raises(OverflowError):
        date.min - dt.timedelta(days=1)


def test_unsupported_operands() -> None:
    value = date(2083, 1, 1)
    with pytest.raises(TypeError):
        _ = value + 1  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = value - 1  # type: ignore[operator]


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_roundtrip(protocol: int) -> None:
    value = date(2083, 6, 15)
    restored = pickle.loads(pickle.dumps(value, protocol))
    assert restored == value
    assert type(restored) is date


def test_pickle_format_is_stable() -> None:
    # Golden bytes: changing these breaks existing pickles.
    assert pickle.dumps(date(2083, 6, 15), 2) == (
        b"\x80\x02csambat\ndate\nq\x00M#\x08K\x06K\x0f\x87q\x01Rq\x02."
    )


def test_copy_and_deepcopy() -> None:
    value = date(2083, 6, 15)
    assert copy.copy(value) == value
    assert copy.deepcopy(value) == value


class MyDate(date):
    __slots__ = ()


def test_subclass_preserved() -> None:
    value = MyDate(2083, 6, 15)
    assert type(value + dt.timedelta(days=1)) is MyDate
    assert type(value - dt.timedelta(days=1)) is MyDate
    assert type(value.replace(day=1)) is MyDate
    assert type(MyDate.fromordinal(value.toordinal())) is MyDate
    assert type(MyDate.fromisoformat("2083-06-15")) is MyDate
    assert type(MyDate.from_gregorian(dt.date(2026, 10, 1))) is MyDate
    assert repr(value).endswith("MyDate(2083, 6, 15)")


def test_from_gregorian_accepts_datetime_and_rejects_others() -> None:
    assert date.from_gregorian(dt.datetime(2026, 10, 1, 23, 59)) == date(2083, 6, 15)
    with pytest.raises(TypeError, match=r"datetime\.date"):
        date.from_gregorian("2026-10-01")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="out of range"):
        date.from_gregorian(dt.date(1900, 1, 1))


def test_format_dunder() -> None:
    value = date(2083, 6, 15)
    assert f"{value}" == "2083-06-15"
    assert f"{value:%d %B}" == "15 Ashwin"
    with pytest.raises(TypeError):
        value.__format__(1)  # type: ignore[arg-type]


def test_isocalendar_returns_named_tuple() -> None:
    result = date(2083, 6, 15).isocalendar()
    assert tuple(result) == (2083, 25, 4)
    assert (result.year, result.week, result.weekday) == (2083, 25, 4)  # type: ignore[attr-defined]
    assert type(result) is sambat.IsoCalendarDate
