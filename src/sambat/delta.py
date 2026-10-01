"""Calendar arithmetic in BS months and years.

``timedelta`` measures exact days. Adding "one month" in the Bikram Sambat
calendar needs a rule, because months have 29 to 32 days.
:class:`relativedelta` follows the semantics of ``dateutil.relativedelta``,
applied to BS fields: years and months are added first, the day is then
clamped to the length of the resulting month, and finally days, weeks and
time are added.

Examples:
    >>> from sambat import date
    >>> from sambat.delta import add_months, diff, relativedelta
    >>> date(2083, 3, 32) + relativedelta(months=1)  # Asar 32 -> Shrawan has 31 days
    sambat.date(2083, 4, 31)
    >>> add_months(date(2083, 3, 32), 1, overflow="raise")
    Traceback (most recent call last):
        ...
    ValueError: day must be in 1..31 for BS 2083-04, not 32
    >>> diff(date(2056, 4, 12), date(2083, 6, 15))
    relativedelta(years=+27, months=+2, days=+3)
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Literal, TypeVar, cast, overload

from sambat import _lookup
from sambat._date import date
from sambat._datetime import datetime

__all__ = [
    "FR",
    "MO",
    "SA",
    "SU",
    "TH",
    "TU",
    "WE",
    "Weekday",
    "add_months",
    "add_years",
    "diff",
    "relativedelta",
]

_DateT = TypeVar("_DateT", bound=date)
_MONTHS = 12
_WEEKDAY_NAMES = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")


class Weekday:
    """A weekday, optionally with an occurrence ``n`` (``FR(+1)``, ``MO(-2)``).

    Used as ``relativedelta(weekday=FR(+1))``: move to the next Friday (or
    stay on today if it is a Friday).

    Args:
        weekday: 0 (Monday) to 6 (Sunday).
        n: Which occurrence; positive looks forward, negative backward.
    """

    __slots__ = ("n", "weekday")

    weekday: int
    n: int | None

    def __init__(self, weekday: int, n: int | None = None) -> None:
        if not 0 <= weekday <= 6:
            message = f"weekday must be in 0..6, not {weekday}"
            raise ValueError(message)
        if n == 0:
            message = "Can't create weekday with n == 0"
            raise ValueError(message)
        self.weekday = weekday
        self.n = n

    def __call__(self, n: int) -> Weekday:
        """Return this weekday with occurrence ``n``."""
        return Weekday(self.weekday, n)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Weekday):
            return NotImplemented
        return (self.weekday, self.n) == (other.weekday, other.n)

    def __hash__(self) -> int:
        return hash((self.weekday, self.n))

    def __repr__(self) -> str:
        name = _WEEKDAY_NAMES[self.weekday]
        return name if self.n is None else f"{name}({self.n:+d})"


MO, TU, WE, TH, FR, SA, SU = (Weekday(index) for index in range(7))


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


class relativedelta:
    """A duration in BS calendar units, with optional absolute fields.

    Relative fields (plural: ``years``, ``months``, ``weeks``, ``days``,
    ``hours``, ...) are added; absolute fields (singular: ``year``, ``month``,
    ``day``, ``weekday``, ``hour``, ...) replace the corresponding value.

    ``relativedelta(dt1, dt2)`` computes the difference ``dt1 - dt2`` such
    that ``dt2 + relativedelta(dt1, dt2) == dt1``.

    Raises:
        TypeError: If ``dt1``/``dt2`` are not sambat dates or a field is not an integer.
    """

    __slots__ = (
        "day",
        "days",
        "hour",
        "hours",
        "microsecond",
        "microseconds",
        "minute",
        "minutes",
        "month",
        "months",
        "second",
        "seconds",
        "weekday",
        "year",
        "years",
    )

    years: int
    months: int
    days: int
    hours: int
    minutes: int
    seconds: int
    microseconds: int
    year: int | None
    month: int | None
    day: int | None
    weekday: Weekday | None
    hour: int | None
    minute: int | None
    second: int | None
    microsecond: int | None

    def __init__(
        self,
        dt1: date | None = None,
        dt2: date | None = None,
        *,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        weekday: Weekday | int | None = None,
        hour: int | None = None,
        minute: int | None = None,
        second: int | None = None,
        microsecond: int | None = None,
    ) -> None:
        self.years, self.months, self.days = int(years), int(months), int(days) + int(weeks) * 7
        self.hours, self.minutes = int(hours), int(minutes)
        self.seconds, self.microseconds = int(seconds), int(microseconds)
        self.year, self.month, self.day = year, month, day
        self.hour, self.minute, self.second, self.microsecond = hour, minute, second, microsecond
        self.weekday = Weekday(weekday) if isinstance(weekday, int) else weekday
        if month is not None and not 1 <= month <= _MONTHS:
            message = f"month must be in 1..12, not {month}"
            raise ValueError(message)
        if dt1 is not None or dt2 is not None:
            if not (isinstance(dt1, date) and isinstance(dt2, date)):
                message = "relativedelta(dt1, dt2) requires two sambat date or datetime objects"
                raise TypeError(message)
            self._set_difference(dt1, dt2)
        self._normalize()

    # ---------------------------------------------------------------- helpers

    def _normalize(self) -> None:
        for small, large, size in (
            ("microseconds", "seconds", 1_000_000),
            ("seconds", "minutes", 60),
            ("minutes", "hours", 60),
            ("hours", "days", 24),
        ):
            value = getattr(self, small)
            if abs(value) >= size:
                carry, remainder = divmod(abs(value), size)
                setattr(self, small, remainder * _sign(value))
                setattr(self, large, getattr(self, large) + carry * _sign(value))
        if abs(self.months) >= _MONTHS:
            sign = _sign(self.months)
            carry, remainder = divmod(abs(self.months), _MONTHS)
            self.months = remainder * sign
            self.years += carry * sign

    def _set_difference(self, dt1: date, dt2: date) -> None:
        if isinstance(dt1, datetime) != isinstance(dt2, datetime):
            dt1, dt2 = _as_datetime(dt1), _as_datetime(dt2)
        total_months = (dt1.year - dt2.year) * _MONTHS + (dt1.month - dt2.month)
        self.years, self.months = divmod(abs(total_months), _MONTHS)
        self._apply_sign(total_months)
        moved = dt2 + self
        later = dt1 > dt2
        while (dt1 < moved) if later else (dt1 > moved):
            total_months += -1 if later else 1
            self.years, self.months = divmod(abs(total_months), _MONTHS)
            self._apply_sign(total_months)
            moved = dt2 + self
        # Split the remaining time into fields that all share one sign.
        total = (dt1 - moved) // _dt.timedelta(microseconds=1)
        sign = _sign(total)
        rest, self.microseconds = divmod(abs(total), 1_000_000)
        rest, self.seconds = divmod(rest, 60)
        rest, self.minutes = divmod(rest, 60)
        self.days, self.hours = divmod(rest, 24)
        for name in ("days", "hours", "minutes", "seconds", "microseconds"):
            setattr(self, name, getattr(self, name) * sign)

    def _apply_sign(self, total_months: int) -> None:
        if total_months < 0:
            self.years, self.months = -self.years, -self.months

    def _fields(self) -> tuple[Any, ...]:
        return tuple(getattr(self, name) for name in self.__slots__)

    def _has_time(self) -> bool:
        return bool(self.hours or self.minutes or self.seconds or self.microseconds) or any(
            value is not None for value in (self.hour, self.minute, self.second, self.microsecond)
        )

    # ------------------------------------------------------------- operations

    def _apply(self, other: _DateT, *, clamp: bool = True) -> _DateT:
        year = (self.year if self.year is not None else other.year) + self.years
        month = self.month if self.month is not None else other.month
        if self.months:
            month += self.months
            if month > _MONTHS:
                year += 1
                month -= _MONTHS
            elif month < 1:
                year -= 1
                month += _MONTHS
        day = self.day if self.day is not None else other.day
        if clamp:
            day = min(_lookup.days_in_month(year, month), day)
        if isinstance(other, datetime):
            result: date = other.replace(
                year=year,
                month=month,
                day=day,
                hour=other.hour if self.hour is None else self.hour,
                minute=other.minute if self.minute is None else self.minute,
                second=other.second if self.second is None else self.second,
                microsecond=other.microsecond if self.microsecond is None else self.microsecond,
            )
        else:
            result = other.replace(year=year, month=month, day=day)
        result = result + _dt.timedelta(
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
            microseconds=self.microseconds,
        )
        if self.weekday is not None:
            target, nth = self.weekday.weekday, self.weekday.n or 1
            jump = (abs(nth) - 1) * 7
            if nth > 0:
                jump += (7 - result.weekday() + target) % 7
            else:
                jump += (result.weekday() - target) % 7
                jump = -jump
            result = result + _dt.timedelta(days=jump)
        return cast("_DateT", result)

    @overload
    def __add__(self, other: relativedelta) -> relativedelta: ...
    @overload
    def __add__(self, other: _DateT) -> _DateT: ...
    def __add__(self, other: Any) -> Any:
        if isinstance(other, relativedelta):
            return relativedelta(
                years=self.years + other.years,
                months=self.months + other.months,
                days=self.days + other.days,
                hours=self.hours + other.hours,
                minutes=self.minutes + other.minutes,
                seconds=self.seconds + other.seconds,
                microseconds=self.microseconds + other.microseconds,
                year=other.year if other.year is not None else self.year,
                month=other.month if other.month is not None else self.month,
                day=other.day if other.day is not None else self.day,
                weekday=other.weekday if other.weekday is not None else self.weekday,
                hour=other.hour if other.hour is not None else self.hour,
                minute=other.minute if other.minute is not None else self.minute,
                second=other.second if other.second is not None else self.second,
                microsecond=other.microsecond
                if other.microsecond is not None
                else self.microsecond,
            )
        if isinstance(other, _dt.timedelta):
            return self + relativedelta(
                days=other.days, seconds=other.seconds, microseconds=other.microseconds
            )
        if isinstance(other, date):
            return self._apply(other)
        return NotImplemented

    def __radd__(self, other: Any) -> Any:
        return self.__add__(other)

    def __rsub__(self, other: Any) -> Any:
        return (-self).__radd__(other)

    def __sub__(self, other: Any) -> Any:
        if not isinstance(other, relativedelta):
            return NotImplemented
        return self + (-other)

    def __neg__(self) -> relativedelta:
        return relativedelta(
            years=-self.years,
            months=-self.months,
            days=-self.days,
            hours=-self.hours,
            minutes=-self.minutes,
            seconds=-self.seconds,
            microseconds=-self.microseconds,
            year=self.year,
            month=self.month,
            day=self.day,
            weekday=self.weekday,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
        )

    def __mul__(self, factor: int) -> relativedelta:
        if not isinstance(factor, int) or isinstance(factor, bool):
            return NotImplemented
        return relativedelta(
            years=self.years * factor,
            months=self.months * factor,
            days=self.days * factor,
            hours=self.hours * factor,
            minutes=self.minutes * factor,
            seconds=self.seconds * factor,
            microseconds=self.microseconds * factor,
            year=self.year,
            month=self.month,
            day=self.day,
            weekday=self.weekday,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
        )

    __rmul__ = __mul__

    def __bool__(self) -> bool:
        return any(value not in (0, None) for value in self._fields())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, relativedelta):
            return NotImplemented
        return self._fields() == other._fields()

    def __hash__(self) -> int:
        return hash(self._fields())

    def __repr__(self) -> str:
        parts = [
            f"{name}={getattr(self, name):+d}"
            for name in ("years", "months", "days", "hours", "minutes", "seconds", "microseconds")
            if getattr(self, name)
        ]
        parts += [
            f"{name}={getattr(self, name)!r}"
            for name in (
                "year",
                "month",
                "day",
                "weekday",
                "hour",
                "minute",
                "second",
                "microsecond",
            )
            if getattr(self, name) is not None
        ]
        return f"relativedelta({', '.join(parts)})"

    def apply(self, value: _DateT, *, overflow: Literal["clamp", "raise"] = "clamp") -> _DateT:
        """Add this delta to ``value``, choosing how to handle short months.

        Args:
            value: A sambat ``date`` or ``datetime``.
            overflow: ``"clamp"`` moves an invalid day to the last day of the
                month (the ``+`` behaviour); ``"raise"`` raises ``ValueError``.

        Returns:
            The shifted value.

        Raises:
            ValueError: If ``overflow="raise"`` and the day does not exist.
        """
        if overflow not in {"clamp", "raise"}:
            message = f"overflow must be 'clamp' or 'raise', not {overflow!r}"
            raise ValueError(message)
        return self._apply(value, clamp=overflow == "clamp")


def _as_datetime(value: date) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime(value.year, value.month, value.day)


def add_months(
    value: _DateT, months: int, *, overflow: Literal["clamp", "raise"] = "clamp"
) -> _DateT:
    """Add ``months`` BS months to ``value``.

    Args:
        value: A sambat ``date`` or ``datetime``.
        months: The number of months to add (may be negative).
        overflow: ``"clamp"`` (default) or ``"raise"`` when the day does not
            exist in the target month.

    Returns:
        The shifted value.
    """
    return relativedelta(months=months).apply(value, overflow=overflow)


def add_years(
    value: _DateT, years: int, *, overflow: Literal["clamp", "raise"] = "clamp"
) -> _DateT:
    """Add ``years`` BS years to ``value`` (same month and day where possible).

    Args:
        value: A sambat ``date`` or ``datetime``.
        years: The number of years to add (may be negative).
        overflow: ``"clamp"`` (default) or ``"raise"`` when the day does not
            exist in the target month.

    Returns:
        The shifted value.
    """
    return relativedelta(years=years).apply(value, overflow=overflow)


def diff(start: date, end: date) -> relativedelta:
    """Return the BS calendar difference from ``start`` to ``end``.

    ``start + diff(start, end) == end`` always holds. Use it for ages:
    ``diff(birth_date, today)``.

    Args:
        start: The earlier (or reference) date.
        end: The later date.

    Returns:
        A :class:`relativedelta` with years, months, days (and time fields
        for datetimes).
    """
    return relativedelta(end, start)
