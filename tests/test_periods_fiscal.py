from __future__ import annotations

import datetime as dt

import pytest

from sambat import MAXYEAR, date, datetime
from sambat.calendar import MONDAY
from sambat.delta import relativedelta
from sambat.fiscal import SHRAWAN, FiscalYear
from sambat.periods import (
    MonthPeriod,
    Period,
    YearPeriod,
    date_range,
    month_end,
    month_start,
    week_end,
    week_start,
    year_end,
    year_start,
)


def test_boundaries() -> None:
    value = date(2083, 3, 10)
    assert month_start(value) == date(2083, 3, 1)
    assert month_end(value) == date(2083, 3, 32)
    assert year_start(value) == date(2083, 1, 1)
    assert year_end(value) == date(2083, 12, 30)
    thursday = date(2083, 6, 15)
    assert week_start(thursday) == date(2083, 6, 11)  # Sunday
    assert week_end(thursday) == date(2083, 6, 17)  # Saturday
    assert week_start(thursday, first=MONDAY) == date(2083, 6, 12)
    with pytest.raises(ValueError, match="first"):
        week_start(thursday, first=7)


def test_boundaries_keep_time() -> None:
    value = datetime(2083, 3, 10, 9, 30)
    assert month_end(value) == datetime(2083, 3, 32, 9, 30)


def test_date_range() -> None:
    days = list(date_range(date(2083, 3, 31), date(2083, 4, 2)))
    assert days == [date(2083, 3, 31), date(2083, 3, 32), date(2083, 4, 1)]
    weekly = list(date_range(date(2083, 1, 1), date(2083, 1, 20), dt.timedelta(days=7)))
    assert weekly == [date(2083, 1, 1), date(2083, 1, 8), date(2083, 1, 15)]
    backwards = list(date_range(date(2083, 1, 3), date(2083, 1, 1), dt.timedelta(days=-1)))
    assert backwards == [date(2083, 1, 3), date(2083, 1, 2)]
    monthly = list(date_range(date(2083, 3, 32), date(2083, 7, 1), relativedelta(months=1)))
    assert monthly == [date(2083, 3, 32), date(2083, 4, 31), date(2083, 5, 31), date(2083, 6, 31)]
    assert list(date_range(date(2083, 1, 1), date(2083, 1, 1))) == []
    with pytest.raises(ValueError, match="zero"):
        list(date_range(date(2083, 1, 1), date(2083, 2, 1), dt.timedelta(0)))


def test_period() -> None:
    period = Period(date(2083, 1, 30), date(2083, 2, 2))
    assert period.days == len(period) == 4
    assert list(period) == list(period.dates())
    assert date(2083, 2, 1) in period
    assert datetime(2083, 2, 2, 23) in period
    assert date(2083, 2, 3) not in period
    assert "2083-02-01" not in period
    assert period == Period(date(2083, 1, 30), date(2083, 2, 2))
    assert period != "period"
    assert len({period, Period(date(2083, 1, 30), date(2083, 2, 2))}) == 1
    assert repr(period) == "Period(sambat.date(2083, 1, 30), sambat.date(2083, 2, 2))"
    with pytest.raises(ValueError, match="precedes"):
        Period(date(2083, 1, 2), date(2083, 1, 1))


def test_month_and_year_periods() -> None:
    month = MonthPeriod(2083, 12)
    assert (month.start, month.end, month.days) == (date(2083, 12, 1), date(2083, 12, 30), 30)
    assert month.prev() == MonthPeriod(2083, 11)
    assert MonthPeriod(2082, 12).next() == MonthPeriod(2083, 1)
    assert MonthPeriod(2083, 1).prev() == MonthPeriod(2082, 12)
    assert MonthPeriod.of(date(2083, 6, 15)) == MonthPeriod(2083, 6)
    assert repr(month) == "MonthPeriod(2083, 12)"
    year = YearPeriod.of(date(2081, 5, 5))
    assert year.days == 366
    assert len(year.months()) == 12
    assert year.next() == YearPeriod(2082)
    assert year.prev().year == 2080
    assert repr(year) == "YearPeriod(2081)"
    with pytest.raises(ValueError, match="out of range"):
        MonthPeriod(2083, 12).next()


def test_fiscal_year_basics() -> None:
    fy = FiscalYear.of(date(2083, 6, 15))
    assert fy == FiscalYear(2083)
    assert fy.label == str(fy) == "2083/84"
    assert fy.label_ne == "२०८३/८४"
    assert fy.start == date(2083, SHRAWAN, 1)
    assert FiscalYear.of(date(2083, 3, 32)) == FiscalYear(2082)
    assert repr(fy) == "FiscalYear(2083)"
    assert fy.next() == FiscalYear(2084)
    assert fy.prev() < fy <= FiscalYear(2083)
    assert fy > fy.prev()
    with pytest.raises(TypeError):
        _ = fy < 2083  # type: ignore[operator]
    assert {fy, FiscalYear(2083)} == {fy}
    assert fy != 2083


def test_fiscal_year_complete() -> None:
    fy = FiscalYear(2082)
    assert fy.end == date(2083, 3, 32)
    assert fy.days == (date(2083, 3, 32) - date(2082, 4, 1)).days + 1
    assert [m.month for m in fy.months()] == [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]
    assert fy.quarter(1) == Period(date(2082, 4, 1), date(2082, 6, 31))
    assert fy.quarter(4) == Period(date(2083, 1, 1), date(2083, 3, 32))
    assert fy.chaumasik(2) == Period(date(2082, 8, 1), date(2082, 11, 30))
    assert fy.half(2) == Period(date(2082, 10, 1), date(2083, 3, 32))
    quarters = [fy.quarter(n) for n in range(1, 5)]
    assert sum(q.days for q in quarters) == fy.days
    chaumasiks = [fy.chaumasik(n) for n in range(1, 4)]
    assert sum(c.days for c in chaumasiks) == fy.days


def test_fiscal_position_queries() -> None:
    fy = FiscalYear(2082)
    value = date(2083, 1, 10)
    assert fy.fiscal_month(value) == 10
    assert fy.quarter_of(value) == 4
    assert fy.chaumasik_of(value) == 3
    assert fy.half_of(value) == 2
    assert value in fy
    assert "2083-01-10" not in fy
    with pytest.raises(ValueError, match="not in fiscal year"):
        fy.fiscal_month(date(2083, 4, 1))
    with pytest.raises(ValueError, match="number must be"):
        fy.quarter(5)


def test_fiscal_year_beyond_table() -> None:
    fy = FiscalYear(MAXYEAR)
    assert fy.quarter(1).start == date(MAXYEAR, 4, 1)
    with pytest.raises(ValueError, match="out of range"):
        _ = fy.end
    with pytest.raises(ValueError, match="out of range"):
        fy.months()
    months = []
    with pytest.raises(ValueError, match="out of range"):
        months.extend(fy.iter_months())
    assert len(months) == 9


def test_fiscal_labels() -> None:
    for label in ("2083/84", "2083-84", "2083/2084", " २०८३/८४ ", "2099/00"):
        assert FiscalYear.from_label(label).start_year in {2083, 2099}
    for bad in ("2083", "2083/85", "2083/2085", "83/84"):
        with pytest.raises(ValueError, match="fiscal year label"):
            FiscalYear.from_label(bad)


def test_custom_start_month() -> None:
    fy = FiscalYear.of(date(2083, 6, 15), start_month=1)
    assert fy.label == "2083"
    assert fy.start == date(2083, 1, 1)
    assert repr(fy) == "FiscalYear(2083, start_month=1)"
    assert fy.quarter_of(date(2083, 6, 15)) == 2
    with pytest.raises(ValueError, match="start_month"):
        FiscalYear(2083, start_month=13)
