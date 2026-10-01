from __future__ import annotations

import datetime as dt
import pickle
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from sambat import NEPAL_TZ, NepalTimeZone

KATHMANDU = ZoneInfo("Asia/Kathmandu")

# Wall times around both offset changes, including the 1919 fold and the 1986 gap.
CRITICAL_WALL_TIMES = [
    dt.datetime(1919, 12, 31, 23, 48, 43),
    dt.datetime(1919, 12, 31, 23, 48, 44),
    dt.datetime(1919, 12, 31, 23, 59, 59),
    dt.datetime(1920, 1, 1, 0, 0, 0),
    dt.datetime(1985, 12, 31, 23, 59, 59),
    dt.datetime(1986, 1, 1, 0, 0, 0),
    dt.datetime(1986, 1, 1, 0, 14, 59),
    dt.datetime(1986, 1, 1, 0, 15, 0),
    dt.datetime(2026, 10, 1, 12, 0, 0),
]


@pytest.mark.parametrize("wall", CRITICAL_WALL_TIMES)
@pytest.mark.parametrize("fold", [0, 1])
def test_matches_zoneinfo_at_transitions(wall: dt.datetime, fold: int) -> None:
    ours = wall.replace(tzinfo=NEPAL_TZ, fold=fold)
    reference = wall.replace(tzinfo=KATHMANDU, fold=fold)
    assert ours.utcoffset() == reference.utcoffset()
    assert ours.tzname() == reference.tzname()
    assert ours.dst() == reference.dst()


@given(st.datetimes(min_value=dt.datetime(1900, 1, 1), max_value=dt.datetime(2100, 1, 1)))
def test_fromutc_matches_zoneinfo(utc: dt.datetime) -> None:
    ours = utc.replace(tzinfo=dt.UTC).astimezone(NEPAL_TZ)
    reference = utc.replace(tzinfo=dt.UTC).astimezone(KATHMANDU)
    assert ours.replace(tzinfo=None) == reference.replace(tzinfo=None)
    assert ours.fold == reference.fold
    assert ours.utcoffset() == reference.utcoffset()


def test_offsets_by_era() -> None:
    assert dt.datetime(1900, 1, 1, tzinfo=NEPAL_TZ).utcoffset() == dt.timedelta(
        hours=5, minutes=41, seconds=16
    )
    assert dt.datetime(1950, 1, 1, tzinfo=NEPAL_TZ).utcoffset() == dt.timedelta(hours=5, minutes=30)
    assert dt.datetime(2000, 1, 1, tzinfo=NEPAL_TZ).utcoffset() == dt.timedelta(hours=5, minutes=45)


def test_none_arguments() -> None:
    assert NEPAL_TZ.utcoffset(None) is None
    assert NEPAL_TZ.dst(None) is None
    assert NEPAL_TZ.tzname(None) is None


def test_fromutc_validation() -> None:
    with pytest.raises(ValueError, match="not self"):
        NEPAL_TZ.fromutc(dt.datetime(2026, 1, 1, tzinfo=dt.UTC))
    with pytest.raises(TypeError):
        NEPAL_TZ.fromutc(dt.date(2026, 1, 1))  # type: ignore[arg-type]


def test_repr_str_and_pickle() -> None:
    assert repr(NEPAL_TZ) == "sambat.NEPAL_TZ"
    assert str(NEPAL_TZ) == "Asia/Kathmandu"
    assert pickle.loads(pickle.dumps(NEPAL_TZ)) is NEPAL_TZ
    assert isinstance(NEPAL_TZ, NepalTimeZone)
