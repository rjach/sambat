from __future__ import annotations

import datetime as dt

import pytest
from hypothesis import assume, given

from sambat import date, datetime
from sambat.delta import (
    FR,
    MO,
    SU,
    Weekday,
    add_months,
    add_years,
    diff,
    relativedelta,
)
from tests.strategies import bs_dates


def test_month_addition_clamps_to_month_length() -> None:
    assert date(2083, 3, 32) + relativedelta(months=1) == date(2083, 4, 31)
    assert date(2083, 3, 32) - relativedelta(months=1) == date(2083, 2, 31)
    assert date(2082, 12, 30) + relativedelta(months=1) == date(2083, 1, 30)
    assert date(2083, 1, 15) - relativedelta(months=1) == date(2082, 12, 15)


def test_overflow_raise() -> None:
    with pytest.raises(ValueError, match="day must be"):
        add_months(date(2083, 3, 32), 1, overflow="raise")
    with pytest.raises(ValueError, match="overflow"):
        relativedelta(months=1).apply(date(2083, 1, 1), overflow="carry")  # type: ignore[arg-type]
    assert add_months(date(2083, 3, 15), 1, overflow="raise") == date(2083, 4, 15)


def test_add_years() -> None:
    assert add_years(date(2081, 2, 32), 1) == date(2082, 2, 31)
    assert add_years(date(2080, 6, 15), -5) == date(2075, 6, 15)


def test_absolute_fields_and_time() -> None:
    value = datetime(2083, 6, 15, 9, 30)
    shifted = value + relativedelta(day=32, hour=0, minute=0, second=0, microsecond=0)
    assert shifted == datetime(2083, 6, 31)
    assert value + relativedelta(year=2080, month=3) == datetime(2080, 3, 15, 9, 30)
    assert value + relativedelta(hours=15) == datetime(2083, 6, 16, 0, 30)
    assert date(2083, 6, 15) + relativedelta(hour=5) == date(2083, 6, 15)


def test_weekday_targets() -> None:
    thursday = date(2083, 6, 15)
    assert thursday + relativedelta(weekday=FR) == date(2083, 6, 16)
    assert thursday + relativedelta(weekday=FR(+2)) == date(2083, 6, 23)
    assert thursday + relativedelta(weekday=MO(-1)) == date(2083, 6, 12)
    assert thursday + relativedelta(weekday=3) == thursday
    assert thursday + relativedelta(day=1, weekday=SU(+1)) == date(2083, 6, 4)
    assert repr(FR(+2)) == "FR(+2)"
    assert repr(MO) == "MO"
    assert FR(1) == Weekday(4, 1)
    assert hash(FR(1)) == hash(Weekday(4, 1))
    with pytest.raises(ValueError, match="n == 0"):
        FR(0)
    with pytest.raises(ValueError, match="weekday"):
        Weekday(7)


def test_normalisation_and_repr() -> None:
    assert relativedelta(months=25) == relativedelta(years=2, months=1)
    assert relativedelta(months=-13) == relativedelta(years=-1, months=-1)
    assert relativedelta(hours=49) == relativedelta(days=2, hours=1)
    assert relativedelta(weeks=2) == relativedelta(days=14)
    assert relativedelta(seconds=-61) == relativedelta(minutes=-1, seconds=-1)
    assert repr(relativedelta(years=1, day=5)) == "relativedelta(years=+1, day=5)"
    assert repr(relativedelta()) == "relativedelta()"
    assert not relativedelta()
    assert relativedelta(month=1)
    with pytest.raises(ValueError, match="month must be"):
        relativedelta(month=13)


def test_arithmetic_between_deltas() -> None:
    a = relativedelta(years=1, months=2, day=3)
    b = relativedelta(months=11, days=4, weekday=FR)
    total = a + b
    assert total == relativedelta(years=2, months=1, days=4, day=3, weekday=FR)
    assert a - a == relativedelta(day=3)
    assert -relativedelta(days=2) == relativedelta(days=-2)
    assert relativedelta(months=2) * 3 == relativedelta(months=6)
    assert 3 * relativedelta(months=2) == relativedelta(months=6)
    assert relativedelta(days=1) + dt.timedelta(hours=25) == relativedelta(days=2, hours=1)
    assert {relativedelta(days=1), relativedelta(days=1)} == {relativedelta(days=1)}
    assert relativedelta(days=1) != "1 day"
    with pytest.raises(TypeError):
        _ = relativedelta(days=1) * 1.5  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = relativedelta(days=1) + 1  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = relativedelta(days=1) - 1  # type: ignore[operator]


def test_diff_dates() -> None:
    assert diff(date(2056, 4, 12), date(2083, 6, 15)) == relativedelta(years=27, months=2, days=3)
    assert diff(date(2083, 6, 15), date(2056, 4, 12)) == relativedelta(
        years=-27, months=-2, days=-3
    )
    assert diff(date(2083, 6, 15), date(2083, 6, 15)) == relativedelta()
    assert relativedelta(date(2083, 6, 15), date(2056, 4, 12)).years == 27


def test_diff_datetimes_and_mixed() -> None:
    start, end = datetime(2080, 1, 1, 10), datetime(2083, 6, 15, 8, 30)
    result = diff(start, end)
    assert start + result == end
    assert end + diff(end, start) == start
    mixed = diff(date(2083, 6, 1), datetime(2083, 6, 15, 12))
    assert mixed == relativedelta(days=14, hours=12)
    with pytest.raises(TypeError, match="sambat date"):
        relativedelta(date(2083, 1, 1), dt.date(2026, 1, 1))  # type: ignore[arg-type]


@given(bs_dates, bs_dates)
def test_diff_property(start: date, end: date) -> None:
    result = diff(start, end)
    assume(abs(result.years) < 100)
    assert start + result == end


@given(bs_dates)
def test_month_addition_always_valid(value: date) -> None:
    for months in (-13, -1, 1, 12):
        try:
            shifted = value + relativedelta(months=months)
        except ValueError:
            continue  # target month outside the supported range
        assert shifted.day <= value.day
        assert shifted.day == min(value.day, shifted.days_in_month())
