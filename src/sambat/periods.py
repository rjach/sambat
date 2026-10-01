"""Month, year and week boundaries, and ranges of BS dates.

Functions that take a ``datetime`` keep its time of day and ``tzinfo``; only
the date part moves.

Examples:
    >>> from sambat import date
    >>> from sambat.periods import MonthPeriod, date_range, month_end
    >>> month_end(date(2083, 3, 10))
    sambat.date(2083, 3, 32)
    >>> MonthPeriod(2083, 6).days
    31
    >>> [str(d) for d in date_range(date(2083, 3, 31), date(2083, 4, 2))]
    ['2083-03-31', '2083-03-32', '2083-04-01']
"""

from __future__ import annotations

import datetime as _dt
from typing import TYPE_CHECKING, Self, TypeVar

from sambat import _lookup
from sambat._date import date
from sambat.calendar import SUNDAY
from sambat.delta import relativedelta

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    "MonthPeriod",
    "Period",
    "YearPeriod",
    "date_range",
    "month_end",
    "month_start",
    "week_end",
    "week_start",
    "year_end",
    "year_start",
]

_DateT = TypeVar("_DateT", bound=date)
_MONTHS = 12


def month_start(value: _DateT) -> _DateT:
    """Return the first day of ``value``'s BS month."""
    return value.replace(day=1)


def month_end(value: _DateT) -> _DateT:
    """Return the last day of ``value``'s BS month."""
    return value.replace(day=_lookup.days_in_month(value.year, value.month))


def year_start(value: _DateT) -> _DateT:
    """Return Baishakh 1 of ``value``'s BS year."""
    return value.replace(month=1, day=1)


def year_end(value: _DateT) -> _DateT:
    """Return the last day of Chaitra in ``value``'s BS year."""
    return value.replace(month=_MONTHS, day=_lookup.days_in_month(value.year, _MONTHS))


def week_start(value: _DateT, *, first: int = SUNDAY) -> _DateT:
    """Return the first day of ``value``'s week.

    Args:
        value: A sambat ``date`` or ``datetime``.
        first: The weekday that starts the week (default Sunday, the Nepali
            convention; 0 = Monday .. 6 = Sunday).

    Returns:
        The start of the week.
    """
    if not 0 <= first <= 6:
        message = f"first must be in 0..6, not {first}"
        raise ValueError(message)
    return value + _dt.timedelta(days=-((value.weekday() - first) % 7))


def week_end(value: _DateT, *, first: int = SUNDAY) -> _DateT:
    """Return the last day of ``value``'s week (see :func:`week_start`)."""
    return week_start(value, first=first) + _dt.timedelta(days=6)


def date_range(
    start: _DateT,
    stop: _DateT,
    step: _dt.timedelta | relativedelta | None = None,
) -> Iterator[_DateT]:
    """Yield values from ``start`` up to, but excluding, ``stop``.

    Like :func:`range`, the interval is half-open and ``step`` may be
    negative. With a :class:`~sambat.delta.relativedelta` step, the n-th value
    is ``start + n * step``, so month steps do not drift after a short month.

    Args:
        start: The first value.
        stop: The exclusive bound.
        step: A ``timedelta`` or ``relativedelta`` (default one day).

    Yields:
        Successive values of the same type as ``start``.

    Raises:
        ValueError: If ``step`` is zero.
    """
    if step is None:
        step = _dt.timedelta(days=1)
    probe = start + step
    if probe == start:
        message = "date_range() step must not be zero"
        raise ValueError(message)
    forward = probe > start
    count = 0
    while True:
        current = start + step * count
        if (forward and current >= stop) or (not forward and current <= stop):
            return
        yield current
        count += 1


class Period:
    """An inclusive range of BS dates, ``start`` to ``end``.

    Args:
        start: The first day.
        end: The last day (must not precede ``start``).
    """

    __slots__ = ("end", "start")

    start: date
    end: date

    def __init__(self, start: date, end: date) -> None:
        if end < start:
            message = f"period end {end} precedes its start {start}"
            raise ValueError(message)
        self.start = start
        self.end = end

    @property
    def days(self) -> int:
        """The number of days in the period."""
        span: _dt.timedelta = self.end - self.start
        return span.days + 1

    def __contains__(self, value: object) -> bool:
        if not isinstance(value, date):
            return False
        day = date(value.year, value.month, value.day)
        return self.start <= day <= self.end

    def dates(self) -> Iterator[date]:
        """Yield every day of the period."""
        return date_range(self.start, self.end + _dt.timedelta(days=1))

    def __iter__(self) -> Iterator[date]:
        return self.dates()

    def __len__(self) -> int:
        return self.days

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return (self.start, self.end) == (other.start, other.end)

    def __hash__(self) -> int:
        return hash((self.start, self.end))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.start!r}, {self.end!r})"


class MonthPeriod(Period):
    """One BS month.

    Args:
        year: The BS year.
        month: The BS month (1..12).

    Examples:
        >>> from sambat.periods import MonthPeriod
        >>> m = MonthPeriod(2083, 3)
        >>> m.start, m.end, m.days
        (sambat.date(2083, 3, 1), sambat.date(2083, 3, 32), 32)
        >>> m.next()
        MonthPeriod(2083, 4)
    """

    __slots__ = ("month", "year")

    year: int
    month: int

    def __init__(self, year: int, month: int) -> None:
        length = _lookup.days_in_month(year, month)
        super().__init__(date(year, month, 1), date(year, month, length))
        self.year = year
        self.month = month

    @classmethod
    def of(cls, value: date) -> Self:
        """Return the month containing ``value``."""
        return cls(value.year, value.month)

    def next(self) -> MonthPeriod:
        """Return the following month."""
        if self.month == _MONTHS:
            return MonthPeriod(self.year + 1, 1)
        return MonthPeriod(self.year, self.month + 1)

    def prev(self) -> MonthPeriod:
        """Return the preceding month."""
        if self.month == 1:
            return MonthPeriod(self.year - 1, _MONTHS)
        return MonthPeriod(self.year, self.month - 1)

    def __repr__(self) -> str:
        return f"MonthPeriod({self.year}, {self.month})"


class YearPeriod(Period):
    """One BS year (Baishakh 1 to the end of Chaitra).

    Args:
        year: The BS year.
    """

    __slots__ = ("year",)

    year: int

    def __init__(self, year: int) -> None:
        end = date(year, _MONTHS, _lookup.days_in_month(year, _MONTHS))
        super().__init__(date(year, 1, 1), end)
        self.year = year

    @classmethod
    def of(cls, value: date) -> Self:
        """Return the year containing ``value``."""
        return cls(value.year)

    def months(self) -> list[MonthPeriod]:
        """Return the twelve months of the year."""
        return [MonthPeriod(self.year, month) for month in range(1, _MONTHS + 1)]

    def next(self) -> YearPeriod:
        """Return the following year."""
        return YearPeriod(self.year + 1)

    def prev(self) -> YearPeriod:
        """Return the preceding year."""
        return YearPeriod(self.year - 1)

    def __repr__(self) -> str:
        return f"YearPeriod({self.year})"
