"""The Bikram Sambat :class:`datetime` type."""

from __future__ import annotations

import datetime as _dt
import time as _time
import warnings
from typing import Any, ClassVar, Self, SupportsIndex

from sambat import _formatting, _isoformat, _lookup, _parsing
from sambat._date import check_int, date
from sambat.locale import EN, Locale

_BSDate = date  # `combine()` and `date()` shadow the name `date`

__all__ = ["datetime"]

_KEEP: Any = object()  # sentinel: "argument not given"
_MAX_HOUR, _MAX_MINUTE, _MAX_SECOND, _MAX_MICROSECOND = 23, 59, 59, 999_999


def _check_time_fields(hour: int, minute: int, second: int, microsecond: int, fold: int) -> None:
    for name, value, upper in (
        ("hour", hour, _MAX_HOUR),
        ("minute", minute, _MAX_MINUTE),
        ("second", second, _MAX_SECOND),
        ("microsecond", microsecond, _MAX_MICROSECOND),
    ):
        if not 0 <= value <= upper:
            message = f"{name} must be in 0..{upper}, not {value}"
            raise ValueError(message)
    if fold not in {0, 1}:
        message = "fold must be either 0 or 1"
        raise ValueError(message)


def _check_tzinfo(tzinfo: object) -> None:
    if tzinfo is not None and not isinstance(tzinfo, _dt.tzinfo):
        message = "tzinfo argument must be None or of a tzinfo subclass"
        raise TypeError(message)


class datetime(date):
    """A Bikram Sambat (BS) date with a time of day and optional time zone.

    ``sambat.datetime`` mirrors :class:`datetime.datetime`. Time-zone handling,
    timestamps, comparisons and hashing are delegated to an equivalent
    Gregorian :class:`datetime.datetime` (see :meth:`to_gregorian`), so any
    ``tzinfo`` implementation (``zoneinfo``, ``dateutil``, ``pytz``) behaves
    exactly as it does with the standard library.

    Args:
        year: BS year in ``MINYEAR..MAXYEAR``.
        month: BS month, 1 (Baishakh) to 12 (Chaitra).
        day: Day of the month, 1 to the month's length (up to 32).
        hour: 0..23.
        minute: 0..59.
        second: 0..59.
        microsecond: 0..999999.
        tzinfo: ``None`` for a naive value, or a :class:`datetime.tzinfo`.
        fold: 0 or 1, disambiguating repeated wall times (PEP 495).

    Examples:
        >>> from sambat import NEPAL_TZ, datetime
        >>> dt = datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ)
        >>> dt.isoformat()
        '2083-06-15T09:30:00+05:45'
        >>> dt.to_gregorian()
        datetime.datetime(2026, 10, 1, 9, 30, tzinfo=sambat.NEPAL_TZ)
    """

    __slots__ = ("_fold", "_hour", "_microsecond", "_minute", "_second", "_twin", "_tzinfo")

    min: ClassVar[datetime]  # pyright: ignore[reportIncompatibleVariableOverride]
    max: ClassVar[datetime]  # pyright: ignore[reportIncompatibleVariableOverride]
    resolution: ClassVar[_dt.timedelta] = _dt.timedelta(microseconds=1)
    _is_datetime: ClassVar[bool] = True

    _hour: int
    _minute: int
    _second: int
    _microsecond: int
    _tzinfo: _dt.tzinfo | None
    _fold: int
    _twin: _dt.datetime | None

    def __new__(
        cls,
        year: SupportsIndex,
        month: SupportsIndex,
        day: SupportsIndex,
        hour: SupportsIndex = 0,
        minute: SupportsIndex = 0,
        second: SupportsIndex = 0,
        microsecond: SupportsIndex = 0,
        tzinfo: _dt.tzinfo | None = None,
        *,
        fold: int = 0,
    ) -> Self:
        y = check_int(year, "year")
        m = check_int(month, "month")
        d = check_int(day, "day")
        fields = (
            check_int(hour, "hour"),
            check_int(minute, "minute"),
            check_int(second, "second"),
            check_int(microsecond, "microsecond"),
        )
        fold = check_int(fold, "fold")
        _check_time_fields(*fields, fold)
        _check_tzinfo(tzinfo)
        self = cls._create(y, m, d, _lookup.ymd_to_ordinal(y, m, d))
        self._hour, self._minute, self._second, self._microsecond = fields
        self._tzinfo = tzinfo
        self._fold = fold
        self._twin = None
        return self

    @classmethod
    def _from_gregorian_datetime(cls, value: _dt.datetime) -> Self:
        year, month, day = _lookup.ordinal_to_ymd(value.toordinal())
        return cls(
            year,
            month,
            day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            value.tzinfo,
            fold=value.fold,
        )

    def _gregorian(self) -> _dt.datetime:
        twin = self._twin
        if twin is None:
            twin = _dt.datetime.combine(
                _dt.date.fromordinal(self._ordinal),
                _dt.time(
                    self._hour, self._minute, self._second, self._microsecond, fold=self._fold
                ),
                self._tzinfo,
            )
            self._twin = twin
        return twin

    def _from_result(self, value: _dt.datetime) -> Self:
        if not _lookup.in_range(value.toordinal()):
            message = "date value out of range"
            raise OverflowError(message)
        return type(self)._from_gregorian_datetime(value)

    # ----------------------------------------------------------- constructors

    @classmethod
    def today(cls) -> Self:
        """Return the current local date and time (naive)."""
        return cls.fromtimestamp(_time.time())

    @classmethod
    def now(cls, tz: _dt.tzinfo | None = None) -> Self:
        """Return the current date and time.

        Args:
            tz: A time zone; when ``None`` the result is naive local time.

        Returns:
            The current BS datetime.
        """
        return cls._from_gregorian_datetime(_dt.datetime.now(tz))

    @classmethod
    def fromtimestamp(cls, timestamp: float, tz: _dt.tzinfo | None = None) -> Self:
        """Return the datetime corresponding to a POSIX timestamp.

        Args:
            timestamp: Seconds since the epoch.
            tz: A time zone; when ``None`` the result is naive local time.

        Returns:
            The BS datetime.
        """
        return cls._from_gregorian_datetime(_dt.datetime.fromtimestamp(timestamp, tz))

    @classmethod
    def utcfromtimestamp(cls, timestamp: float) -> Self:
        """Return the naive UTC datetime for a POSIX timestamp (deprecated, as in Python 3.12).

        Use ``datetime.fromtimestamp(timestamp, tz=UTC)`` instead.
        """
        warnings.warn(
            "datetime.utcfromtimestamp() is deprecated; use timezone-aware objects, "
            "e.g. datetime.fromtimestamp(timestamp, tz=sambat.UTC)",
            DeprecationWarning,
            stacklevel=2,
        )
        value = _dt.datetime.fromtimestamp(timestamp, _dt.UTC).replace(tzinfo=None)
        return cls._from_gregorian_datetime(value)

    @classmethod
    def utcnow(cls) -> Self:
        """Return the current naive UTC datetime (deprecated, as in Python 3.12).

        Use ``datetime.now(tz=UTC)`` instead.
        """
        warnings.warn(
            "datetime.utcnow() is deprecated; use timezone-aware objects, "
            "e.g. datetime.now(tz=sambat.UTC)",
            DeprecationWarning,
            stacklevel=2,
        )
        value = _dt.datetime.now(_dt.UTC).replace(tzinfo=None)
        return cls._from_gregorian_datetime(value)

    @classmethod
    def combine(cls, date: _BSDate, time: _dt.time, tzinfo: _dt.tzinfo | None = _KEEP) -> Self:
        """Combine a BS date and a :class:`datetime.time`.

        Args:
            date: A :class:`sambat.date` (a stdlib ``datetime.date`` is rejected).
            time: The time of day.
            tzinfo: Overrides ``time.tzinfo`` when given.

        Returns:
            The combined BS datetime.

        Raises:
            TypeError: If the arguments have the wrong types.
        """
        if not isinstance(date, _BSDate):
            message = f"combine() argument 1 must be sambat.date, not {type(date).__name__}"
            raise TypeError(message)
        if not isinstance(time, _dt.time):
            message = f"combine() argument 2 must be datetime.time, not {type(time).__name__}"
            raise TypeError(message)
        zone = time.tzinfo if tzinfo is _KEEP else tzinfo
        return cls(
            date.year,
            date.month,
            date.day,
            time.hour,
            time.minute,
            time.second,
            time.microsecond,
            zone,
            fold=time.fold,
        )

    @classmethod
    def fromisoformat(cls, date_string: str, /) -> Self:
        """Parse a BS datetime in any ISO 8601 format accepted by Python 3.11+.

        The date part uses the BS calendar; the separator may be any single
        character; the time part accepts everything ``datetime.time.fromisoformat``
        accepts (including ``Z`` and fractional offsets).

        Args:
            date_string: The string to parse.

        Returns:
            The BS datetime.

        Raises:
            TypeError: If ``date_string`` is not a string.
            ValueError: If the string is malformed or the date is invalid.
        """
        if not isinstance(date_string, str):
            message = "fromisoformat: argument must be str"
            raise TypeError(message)
        (year, month, day), parsed = _isoformat.parse_datetime(date_string)
        if parsed is None:
            return cls(year, month, day)
        return cls(
            year,
            month,
            day,
            parsed.hour,
            parsed.minute,
            parsed.second,
            parsed.microsecond,
            parsed.tzinfo,
            fold=parsed.fold,
        )

    @classmethod
    def strptime(cls, date_string: str, format: str, /, *, locale: Locale = EN) -> Self:  # noqa: A002
        """Parse a BS datetime from a string according to ``format``.

        Args:
            date_string: The string to parse.
            format: A format using the same directives as :meth:`strftime`.
            locale: The locale whose month and weekday names are accepted.

        Returns:
            The BS datetime; aware when the format contains ``%z``.

        Raises:
            ValueError: If the string does not match the format.
        """
        fields = _parsing.strptime(date_string, format, locale)
        return cls(*fields)

    @classmethod
    def from_gregorian(cls, value: _dt.date, /) -> Self:
        """Convert a Gregorian :class:`datetime.datetime` to a BS datetime.

        A plain :class:`datetime.date` is accepted and treated as midnight.

        Args:
            value: The Gregorian value; ``tzinfo`` and ``fold`` are preserved.

        Returns:
            The BS datetime for the same wall time.

        Raises:
            TypeError: If ``value`` is not a :class:`datetime.date`.
            ValueError: If the date is outside the supported range.
        """
        if isinstance(value, _dt.datetime):
            return cls._from_gregorian_datetime(value)
        return super().from_gregorian(value)

    # ------------------------------------------------------------- attributes

    @property
    def hour(self) -> int:
        """Hour (0..23)."""
        return self._hour

    @property
    def minute(self) -> int:
        """Minute (0..59)."""
        return self._minute

    @property
    def second(self) -> int:
        """Second (0..59)."""
        return self._second

    @property
    def microsecond(self) -> int:
        """Microsecond (0..999999)."""
        return self._microsecond

    @property
    def tzinfo(self) -> _dt.tzinfo | None:
        """The time zone, or ``None`` for naive values."""
        return self._tzinfo

    @property
    def fold(self) -> int:
        """0 or 1; selects the earlier or later of two repeated wall times (PEP 495)."""
        return self._fold

    # ---------------------------------------------------------------- queries

    def to_gregorian(self) -> _dt.datetime:
        """Return the Gregorian :class:`datetime.datetime` for the same wall time."""
        return self._gregorian()

    def date(self) -> _BSDate:
        """Return the BS date part as a :class:`sambat.date`."""
        return _BSDate(self._year, self._month, self._day)

    def time(self) -> _dt.time:
        """Return the time part (without ``tzinfo``)."""
        return _dt.time(self._hour, self._minute, self._second, self._microsecond, fold=self._fold)

    def timetz(self) -> _dt.time:
        """Return the time part including ``tzinfo``."""
        return _dt.time(
            self._hour,
            self._minute,
            self._second,
            self._microsecond,
            self._tzinfo,
            fold=self._fold,
        )

    def utcoffset(self) -> _dt.timedelta | None:
        """Return the UTC offset, or ``None`` for naive values."""
        return self._gregorian().utcoffset()

    def dst(self) -> _dt.timedelta | None:
        """Return the DST adjustment, or ``None`` for naive values."""
        return self._gregorian().dst()

    def tzname(self) -> str | None:
        """Return the time zone name, or ``None`` for naive values."""
        return self._gregorian().tzname()

    def timestamp(self) -> float:
        """Return the POSIX timestamp (naive values are taken as local time)."""
        return self._gregorian().timestamp()

    def timetuple(self) -> _time.struct_time:
        """Return a :class:`time.struct_time` with BS date fields."""
        dst = self.dst()
        flag = -1 if dst is None else int(bool(dst))
        return _time.struct_time(
            (
                self._year,
                self._month,
                self._day,
                self._hour,
                self._minute,
                self._second,
                self.weekday(),
                self._day_of_year(),
                flag,
            )
        )

    def utctimetuple(self) -> _time.struct_time:
        """Return a :class:`time.struct_time` in UTC with BS date fields."""
        value = self._gregorian()
        offset = value.utcoffset()
        naive = value.replace(tzinfo=None)
        if offset:
            naive -= offset
        if not _lookup.in_range(naive.toordinal()):
            message = "date value out of range"
            raise OverflowError(message)
        utc = type(self)._from_gregorian_datetime(naive)
        return _time.struct_time((*utc.timetuple()[:8], 0))

    def astimezone(self, tz: _dt.tzinfo | None = None) -> Self:
        """Return the same instant expressed in time zone ``tz``.

        Args:
            tz: The target time zone; ``None`` means the system local zone.

        Returns:
            An aware datetime of the same class.
        """
        return self._from_result(self._gregorian().astimezone(tz))

    def replace(
        self,
        year: SupportsIndex | None = None,
        month: SupportsIndex | None = None,
        day: SupportsIndex | None = None,
        hour: SupportsIndex | None = None,
        minute: SupportsIndex | None = None,
        second: SupportsIndex | None = None,
        microsecond: SupportsIndex | None = None,
        tzinfo: _dt.tzinfo | None = _KEEP,
        *,
        fold: int | None = None,
    ) -> Self:
        """Return a datetime with the given fields replaced.

        Pass ``tzinfo=None`` to make an aware value naive.

        Returns:
            A new instance of the same class.
        """
        return type(self)(
            self._year if year is None else year,
            self._month if month is None else month,
            self._day if day is None else day,
            self._hour if hour is None else hour,
            self._minute if minute is None else minute,
            self._second if second is None else second,
            self._microsecond if microsecond is None else microsecond,
            self._tzinfo if tzinfo is _KEEP else tzinfo,
            fold=self._fold if fold is None else fold,
        )

    # ------------------------------------------------------------- formatting

    def isoformat(self, sep: str = "T", timespec: str = "auto") -> str:
        """Return ``YYYY-MM-DD[sep]HH:MM:SS[.ffffff][+HH:MM]``.

        Args:
            sep: A single character placed between date and time.
            timespec: ``auto``, ``hours``, ``minutes``, ``seconds``,
                ``milliseconds`` or ``microseconds``.

        Returns:
            The ISO 8601 string with the BS date.
        """
        gregorian = self._gregorian().isoformat(sep, timespec)
        return date.isoformat(self) + gregorian[10:]

    def __str__(self) -> str:
        return self.isoformat(sep=" ")

    def ctime(self) -> str:
        """Return a ``time.ctime()``-style string."""
        return self.strftime("%a %b %e %H:%M:%S %Y")

    def strftime(self, format: str, /, *, locale: Locale = EN) -> str:  # noqa: A002
        """Format the datetime; see the directive table in the documentation."""
        return _formatting.strftime(self, format, locale)

    def __repr__(self) -> str:
        fields = [
            self._year,
            self._month,
            self._day,
            self._hour,
            self._minute,
            self._second,
            self._microsecond,
        ]
        while len(fields) > 5 and fields[-1] == 0:
            fields.pop()
        cls = type(self)
        text = f"{cls.__module__}.{cls.__qualname__}({', '.join(map(str, fields))}"
        if self._tzinfo is not None:
            text += f", tzinfo={self._tzinfo!r}"
        if self._fold:
            text += ", fold=1"
        return text + ")"

    # ------------------------------------------------------------- comparison

    def __eq__(self, other: object) -> bool:
        if isinstance(other, datetime):
            return self._gregorian() == other._gregorian()
        if isinstance(other, date):
            return False
        return NotImplemented

    def _ordered(self, other: object) -> _dt.datetime | None:
        if isinstance(other, datetime):
            return other._gregorian()
        if isinstance(other, date):
            message = f"can't compare {type(self).__name__} to {type(other).__name__}"
            raise TypeError(message)
        return None

    def __lt__(self, other: object) -> bool:
        peer = self._ordered(other)
        return NotImplemented if peer is None else self._gregorian() < peer

    def __le__(self, other: object) -> bool:
        peer = self._ordered(other)
        return NotImplemented if peer is None else self._gregorian() <= peer

    def __gt__(self, other: object) -> bool:
        peer = self._ordered(other)
        return NotImplemented if peer is None else self._gregorian() > peer

    def __ge__(self, other: object) -> bool:
        peer = self._ordered(other)
        return NotImplemented if peer is None else self._gregorian() >= peer

    def __hash__(self) -> int:
        if self._hashcode == -1:
            self._hashcode = hash(self._gregorian())
        return self._hashcode

    # ------------------------------------------------------------- arithmetic

    def __add__(self, other: _dt.timedelta) -> Self:
        if not isinstance(other, _dt.timedelta):
            return NotImplemented
        try:
            result = self._gregorian() + other
        except OverflowError:
            message = "date value out of range"
            raise OverflowError(message) from None
        return self._from_result(result)

    __radd__ = __add__

    def __sub__(self, other: Any) -> Any:
        if isinstance(other, _dt.timedelta):
            return self + -other
        if isinstance(other, datetime):
            return self._gregorian() - other._gregorian()
        return NotImplemented

    # ---------------------------------------------------------------- pickling

    def __reduce__(self) -> tuple[Any, ...]:
        args = (
            self._year,
            self._month,
            self._day,
            self._hour,
            self._minute,
            self._second,
            self._microsecond,
            self._tzinfo,
        )
        return type(self), args, {"fold": self._fold} if self._fold else None

    def __setstate__(self, state: dict[str, int]) -> None:
        fold = state.get("fold", 0)
        _check_time_fields(0, 0, 0, 0, fold)
        self._fold = fold
        self._twin = None
        self._hashcode = -1


datetime.__module__ = "sambat"
datetime.min = datetime(_lookup.MINYEAR, 1, 1)
datetime.max = datetime(
    _lookup.MAXYEAR, 12, _lookup.days_in_month(_lookup.MAXYEAR, 12), 23, 59, 59, 999_999
)
