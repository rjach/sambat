"""Hypothesis strategies shared by the test suite."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from hypothesis import strategies as st

import sambat
from sambat import _lookup

ordinals = st.integers(_lookup.MIN_ORDINAL, _lookup.MAX_ORDINAL)
bs_dates = ordinals.map(sambat.date.fromordinal)
timezones = st.sampled_from(
    [
        None,
        dt.UTC,
        sambat.NEPAL_TZ,
        dt.timezone(dt.timedelta(hours=-5, minutes=-30)),
        ZoneInfo("America/New_York"),
        ZoneInfo("Asia/Kathmandu"),
    ]
)


@st.composite
def bs_datetimes(draw: st.DrawFn, *, aware: bool | None = None) -> sambat.datetime:
    day = draw(bs_dates)
    clock = draw(st.times())
    zone = draw(timezones)
    if aware is True and zone is None:
        zone = dt.UTC
    if aware is False:
        zone = None
    return sambat.datetime.combine(day, clock, zone).replace(fold=draw(st.integers(0, 1)))
