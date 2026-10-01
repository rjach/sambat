"""Differential and round-trip properties against the standard library."""

from __future__ import annotations

import copy
import datetime as dt
import pickle

from hypothesis import assume, given
from hypothesis import strategies as st

import sambat
from sambat import _lookup, date, datetime
from sambat.locale import EN, NE
from tests.strategies import bs_dates, bs_datetimes, ordinals

day_deltas = st.integers(-40_000, 40_000).map(lambda days: dt.timedelta(days=days))


@given(ordinals)
def test_ordinal_round_trip(ordinal: int) -> None:
    value = date.fromordinal(ordinal)
    assert value.toordinal() == ordinal
    assert value.to_gregorian().toordinal() == ordinal
    assert date(value.year, value.month, value.day) == value


@given(bs_dates)
def test_matches_gregorian_twin(value: date) -> None:
    twin = value.to_gregorian()
    assert value.weekday() == twin.weekday()
    assert value.isoweekday() == twin.isoweekday()
    assert hash(value) == hash(twin)
    assert date.from_gregorian(twin) == value


@given(bs_dates, bs_dates)
def test_ordering_matches_gregorian(a: date, b: date) -> None:
    assert (a < b) == (a.to_gregorian() < b.to_gregorian())
    assert (a == b) == (a.to_gregorian() == b.to_gregorian())
    assert a - b == a.to_gregorian() - b.to_gregorian()


@given(bs_dates, day_deltas)
def test_addition_matches_gregorian(value: date, delta: dt.timedelta) -> None:
    target = value.toordinal() + delta.days
    assume(_lookup.in_range(target))
    assert (value + delta).to_gregorian() == value.to_gregorian() + delta
    assert (value + delta) - delta == value


@given(bs_dates)
def test_isoformat_round_trip(value: date) -> None:
    assert date.fromisoformat(value.isoformat()) == value
    assert date.fromisoformat(value.strftime("%Y%m%d")) == value


@given(bs_dates)
def test_isocalendar_round_trip(value: date) -> None:
    try:
        year, week, day = value.isocalendar()
    except ValueError:
        # The first days of MINYEAR belong to a week-year that is not supported.
        assert value.year == sambat.MINYEAR
        return
    assert date.fromisocalendar(year, week, day) == value
    assert day == value.isoweekday()
    assert 1 <= week <= 53


@given(bs_dates, st.sampled_from([EN, NE]))
def test_strftime_strptime_round_trip(value: date, locale: sambat.locale.Locale) -> None:
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%A %e %b %Y", "%Y-%j", "%OY %Om %Od"):
        text = value.strftime(fmt, locale=locale)
        assert date.strptime(text, fmt, locale=locale) == value


@given(bs_dates)
def test_week_number_directives_round_trip(value: date) -> None:
    for fmt in ("%Y %U %w", "%Y %W %u"):
        assert date.strptime(value.strftime(fmt), fmt) == value


@given(bs_datetimes())
def test_datetime_matches_gregorian_twin(value: datetime) -> None:
    twin = value.to_gregorian()
    assert value.utcoffset() == twin.utcoffset()
    assert value.tzname() == twin.tzname()
    assert hash(value) == hash(twin)
    assert value.time() == twin.time()
    assert value.isoformat()[10:] == twin.isoformat()[10:]
    assert value.strftime("%H:%M:%S.%f%z") == twin.strftime("%H:%M:%S.%f%z")


@given(bs_datetimes(aware=True), bs_datetimes(aware=True))
def test_aware_comparison_matches_gregorian(a: datetime, b: datetime) -> None:
    assert (a < b) == (a.to_gregorian() < b.to_gregorian())
    assert (a == b) == (a.to_gregorian() == b.to_gregorian())
    assert a - b == a.to_gregorian() - b.to_gregorian()


@given(bs_datetimes())
def test_datetime_iso_and_pickle_round_trip(value: datetime) -> None:
    assert datetime.fromisoformat(value.isoformat()) == value
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        restored = pickle.loads(pickle.dumps(value, protocol))
        assert restored == value
        assert restored.fold == value.fold
    assert copy.deepcopy(value) == value


@given(bs_datetimes(aware=True), st.sampled_from([dt.UTC, sambat.NEPAL_TZ]))
def test_astimezone_preserves_instant(value: datetime, zone: dt.tzinfo) -> None:
    target = value.to_gregorian().astimezone(zone)
    assume(_lookup.in_range(target.toordinal()))
    converted = value.astimezone(zone)
    assert converted == value
    assert converted.to_gregorian() == target
