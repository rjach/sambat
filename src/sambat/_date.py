"""The Bikram Sambat :class:`date` type."""

from __future__ import annotations

import datetime as _dt
import time as _time
from operator import index as _index
from typing import Any, ClassVar, Self, SupportsIndex

from sambat import _formatting, _isoformat, _lookup, _parsing
from sambat.locale import EN, Locale

__all__ = ["IsoCalendarDate", "date"]

#: The tuple type returned by :meth:`date.isocalendar` (the stdlib's own type).
IsoCalendarDate: Any = type(_dt.date(2000, 1, 1).isocalendar())


def check_int(value: object, name: str) -> int:
    if isinstance(value, float):
        message = f"integer argument expected, got float ({name})"
        raise TypeError(message)
    try:
        return _index(value)  # type: ignore[arg-type]
    except TypeError:
        message = f"{name} must be an integer, not {type(value).__name__}"
        raise TypeError(message) from None


class date:
    """A Bikram Sambat (BS) calendar date.

    ``sambat.date`` mirrors :class:`datetime.date`: same constructors,
    methods, operators and error types, with ``year``, ``month`` and ``day``
    in the BS calendar. :meth:`toordinal` returns the same day number as the
    standard library, so ``weekday()``, arithmetic and conversion agree
    exactly with the Gregorian equivalent.

    Args:
        year: BS year in ``MINYEAR..MAXYEAR``.
        month: BS month, 1 (Baishakh) to 12 (Chaitra).
        day: Day of the month, 1 to the month's length (up to 32).

    Raises:
        TypeError: If an argument is not an integer.
        ValueError: If the date does not exist or is outside the supported range.

    Examples:
        >>> from sambat import date
        >>> d = date(2083, 6, 15)
        >>> d.to_gregorian()
        datetime.date(2026, 10, 1)
        >>> d.strftime("%A, %d %B %Y")
        'Thursday, 15 Ashwin 2083'
        >>> date.from_gregorian(__import__("datetime").date(2026, 4, 14))
        sambat.date(2083, 1, 1)
    """

    __slots__ = ("_day", "_hashcode", "_month", "_ordinal", "_year")

    min: ClassVar[date]
    max: ClassVar[date]
    resolution: ClassVar[_dt.timedelta] = _dt.timedelta(days=1)

    # True on sambat.datetime; lets date-only operations reject datetimes
    # without importing the subclass (CPython treats date and datetime as
    # incomparable even though one subclasses the other).
    _is_datetime: ClassVar[bool] = False

    _year: int
    _month: int
    _day: int
    _ordinal: int
    _hashcode: int

    def __new__(cls, year: SupportsIndex, month: SupportsIndex, day: SupportsIndex) -> Self:
        y = check_int(year, "year")
        m = check_int(month, "month")
        d = check_int(day, "day")
        return cls._create(y, m, d, _lookup.ymd_to_ordinal(y, m, d))

    @classmethod
    def _create(cls, year: int, month: int, day: int, ordinal: int) -> Self:
        self = object.__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._ordinal = ordinal
        self._hashcode = -1
        return self

    @classmethod
    def _from_ordinal(cls, ordinal: int) -> Self:
        year, month, day = _lookup.ordinal_to_ymd(ordinal)
        return cls(year, month, day)

    # ----------------------------------------------------------- constructors

    @classmethod
    def today(cls) -> Self:
        """Return the current local date (in the machine's time zone)."""
        return cls.fromtimestamp(_time.time())

    @classmethod
    def fromtimestamp(cls, timestamp: float, /) -> Self:
        """Return the local date corresponding to a POSIX timestamp.

        Args:
            timestamp: Seconds since the epoch, as returned by ``time.time()``.

        Returns:
            The BS date in the machine's local time zone.
        """
        return cls.fromordinal(_dt.date.fromtimestamp(timestamp).toordinal())

    @classmethod
    def fromordinal(cls, n: int, /) -> Self:
        """Return the date for a proleptic Gregorian ordinal.

        Args:
            n: A day number as returned by :meth:`toordinal`.

        Returns:
            The BS date.

        Raises:
            ValueError: If the ordinal is outside the supported range.
        """
        return cls._from_ordinal(check_int(n, "ordinal"))

    @classmethod
    def fromisoformat(cls, date_string: str, /) -> Self:
        """Parse a BS date in any ISO 8601 format accepted by Python 3.11+.

        Accepted forms are ``YYYY-MM-DD``, ``YYYYMMDD``, ``YYYY-Www``,
        ``YYYY-Www-D``, ``YYYYWww`` and ``YYYYWwwD`` (week dates use the BS week
        calendar of :meth:`isocalendar`).

        Args:
            date_string: The string to parse.

        Returns:
            The BS date.

        Raises:
            TypeError: If ``date_string`` is not a string.
            ValueError: If the string is malformed or the date is invalid.
        """
        if not isinstance(date_string, str):
            message = "fromisoformat: argument must be str"
            raise TypeError(message)
        return cls(*_isoformat.parse_date(date_string))

    @classmethod
    def fromisocalendar(cls, year: int, week: int, day: int) -> Self:
        """Return the date for a BS week-numbering year, week and weekday.

        Args:
            year: The BS week-numbering year.
            week: The week number (1..53).
            day: The ISO weekday (1 = Monday .. 7 = Sunday).

        Returns:
            The BS date.

        Raises:
            ValueError: If the combination is invalid or out of range.
        """
        y = check_int(year, "year")
        w = check_int(week, "week")
        d = check_int(day, "day")
        return cls._from_ordinal(_lookup.week_to_ordinal(y, w, d))

    @classmethod
    def strptime(cls, date_string: str, format: str, /, *, locale: Locale = EN) -> Self:  # noqa: A002
        """Parse a BS date from a string according to ``format``.

        Time directives are accepted and ignored, as in :meth:`datetime.date.strptime`.

        Args:
            date_string: The string to parse.
            format: A format using the same directives as :meth:`strftime`.
            locale: The locale whose month and weekday names are accepted.

        Returns:
            The BS date.

        Raises:
            ValueError: If the string does not match the format.
        """
        fields = _parsing.strptime(date_string, format, locale)
        return cls(fields.year, fields.month, fields.day)

    @classmethod
    def from_gregorian(cls, value: _dt.date, /) -> Self:
        """Convert a Gregorian :class:`datetime.date` to a BS date.

        A :class:`datetime.datetime` is accepted and its date part is used.

        Args:
            value: The Gregorian date.

        Returns:
            The BS date for the same day.

        Raises:
            TypeError: If ``value`` is not a :class:`datetime.date`.
            ValueError: If the date is outside the supported range.
        """
        if not isinstance(value, _dt.date):
            message = f"from_gregorian() expects a datetime.date, not {type(value).__name__}"
            raise TypeError(message)
        return cls._from_ordinal(value.toordinal())

    # ------------------------------------------------------------- attributes

    @property
    def year(self) -> int:
        """BS year (``MINYEAR``..``MAXYEAR``)."""
        return self._year

    @property
    def month(self) -> int:
        """BS month (1 = Baishakh .. 12 = Chaitra)."""
        return self._month

    @property
    def day(self) -> int:
        """Day of the month (1..32)."""
        return self._day

    # ---------------------------------------------------------------- queries

    def toordinal(self) -> int:
        """Return the proleptic Gregorian ordinal (identical to the stdlib's)."""
        return self._ordinal

    def to_gregorian(self) -> _dt.date:
        """Return the Gregorian :class:`datetime.date` for the same day."""
        return _dt.date.fromordinal(self._ordinal)

    def weekday(self) -> int:
        """Return the day of the week, Monday == 0 ... Sunday == 6."""
        return (self._ordinal + 6) % 7

    def isoweekday(self) -> int:
        """Return the day of the week, Monday == 1 ... Sunday == 7."""
        return self.weekday() + 1

    def isocalendar(self) -> tuple[int, int, int]:
        """Return the BS week calendar ``(year, week, weekday)``.

        Weeks run Monday to Sunday and week 1 is the week that contains the
        first Thursday of the BS year (the ISO 8601 rule applied to BS years).
        For the Gregorian ISO week use ``to_gregorian().isocalendar()``.

        Returns:
            An ``IsoCalendarDate`` named tuple.
        """
        result: tuple[int, int, int] = IsoCalendarDate(*_lookup.ordinal_to_week(self._ordinal))
        return result

    def timetuple(self) -> _time.struct_time:
        """Return a :class:`time.struct_time` with BS fields.

        ``tm_yday`` is the day of the BS year and ``tm_isdst`` is ``-1``. Do not
        pass the result to :func:`time.mktime`, which assumes Gregorian fields.
        """
        return _time.struct_time(
            (self._year, self._month, self._day, 0, 0, 0, self.weekday(), self._day_of_year(), -1)
        )

    def _day_of_year(self) -> int:
        return _lookup.days_before_month(self._year, self._month) + self._day

    def days_in_month(self) -> int:
        """Return the number of days (29..32) in this date's BS month."""
        return _lookup.days_in_month(self._year, self._month)

    def days_in_year(self) -> int:
        """Return the number of days (365 or 366) in this date's BS year."""
        return _lookup.days_in_year(self._year)

    def replace(
        self,
        year: SupportsIndex | None = None,
        month: SupportsIndex | None = None,
        day: SupportsIndex | None = None,
    ) -> Self:
        """Return a date with the given fields replaced.

        Args:
            year: New BS year.
            month: New BS month.
            day: New day of the month.

        Returns:
            A new instance of the same class.
        """
        return type(self)(
            self._year if year is None else year,
            self._month if month is None else month,
            self._day if day is None else day,
        )

    def __replace__(self, /, **changes: Any) -> Self:
        return self.replace(**changes)

    # ------------------------------------------------------------- formatting

    def isoformat(self) -> str:
        """Return the date as ``YYYY-MM-DD``."""
        return f"{self._year:04d}-{self._month:02d}-{self._day:02d}"

    __str__ = isoformat

    def ctime(self) -> str:
        """Return a ``time.ctime()``-style string, e.g. ``'Thu Ash 15 00:00:00 2083'``."""
        return self.strftime("%a %b %e %H:%M:%S %Y")

    def strftime(self, format: str, /, *, locale: Locale = EN) -> str:  # noqa: A002
        """Format the date; see the directive table in the documentation.

        Args:
            format: The format string.
            locale: Names, digits and templates to use (default :data:`~sambat.locale.EN`).

        Returns:
            The formatted string.

        Raises:
            ValueError: If the format contains an unknown directive.
        """
        return _formatting.strftime(self, format, locale)

    def __format__(self, fmt: str) -> str:
        if not isinstance(fmt, str):
            message = f"must be str, not {type(fmt).__name__}"
            raise TypeError(message)
        if fmt:
            return self.strftime(fmt)
        return str(self)

    def __repr__(self) -> str:
        cls = type(self)
        return f"{cls.__module__}.{cls.__qualname__}({self._year}, {self._month}, {self._day})"

    # ------------------------------------------------------------- comparison

    def _peer(self, other: object) -> date | None:
        if isinstance(other, date) and not other._is_datetime:
            return other
        return None

    def __eq__(self, other: object) -> bool:
        peer = self._peer(other)
        return NotImplemented if peer is None else self._ordinal == peer._ordinal

    def __lt__(self, other: object) -> bool:
        peer = self._peer(other)
        return NotImplemented if peer is None else self._ordinal < peer._ordinal

    def __le__(self, other: object) -> bool:
        peer = self._peer(other)
        return NotImplemented if peer is None else self._ordinal <= peer._ordinal

    def __gt__(self, other: object) -> bool:
        peer = self._peer(other)
        return NotImplemented if peer is None else self._ordinal > peer._ordinal

    def __ge__(self, other: object) -> bool:
        peer = self._peer(other)
        return NotImplemented if peer is None else self._ordinal >= peer._ordinal

    def __hash__(self) -> int:
        if self._hashcode == -1:
            self._hashcode = hash(self.to_gregorian())
        return self._hashcode

    # ------------------------------------------------------------- arithmetic

    def __add__(self, other: _dt.timedelta) -> Self:
        if not isinstance(other, _dt.timedelta):
            return NotImplemented
        ordinal = self._ordinal + other.days
        if not _lookup.in_range(ordinal):
            message = "date value out of range"
            raise OverflowError(message)
        return type(self).fromordinal(ordinal)

    __radd__ = __add__

    def __sub__(self, other: Any) -> Any:
        if isinstance(other, _dt.timedelta):
            return self + _dt.timedelta(-other.days)
        peer = self._peer(other)
        if peer is not None:
            return _dt.timedelta(self._ordinal - peer._ordinal)
        return NotImplemented

    # ---------------------------------------------------------------- pickling

    def __reduce__(self) -> tuple[type[Self], tuple[int, int, int]]:
        return type(self), (self._year, self._month, self._day)


date.__module__ = "sambat"
date.min = date(_lookup.MINYEAR, 1, 1)
date.max = date(_lookup.MAXYEAR, 12, _lookup.days_in_month(_lookup.MAXYEAR, 12))
