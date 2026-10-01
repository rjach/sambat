"""Pure-Python ``strftime`` for Bikram Sambat dates.

The directive set is fixed and identical on every platform; the C library is
never called. Unknown directives raise ``ValueError`` instead of being echoed.
"""

from __future__ import annotations

import datetime as _dt
from typing import TYPE_CHECKING, Protocol

from sambat import _lookup
from sambat.text import DEVANAGARI_DIGITS

if TYPE_CHECKING:
    from collections.abc import Callable

    from sambat.locale import Locale

__all__ = ["format_offset", "strftime"]

# Directives whose output is a number and may be rendered with other digits.
NUMERIC_DIRECTIVES = frozenset("CdeGHIjmMSUuVWwyYf")
# Directives that expand to other directives.
_COMPOSITES = {"D": "%m/%d/%y", "F": "%Y-%m-%d", "r": "%I:%M:%S %p", "R": "%H:%M", "T": "%H:%M:%S"}
_TO_DEVANAGARI = str.maketrans("0123456789", DEVANAGARI_DIGITS)
_NOON = 12


class _DateLike(Protocol):
    """The part of the ``sambat.date`` interface that formatting needs."""

    @property
    def year(self) -> int: ...
    @property
    def month(self) -> int: ...
    @property
    def day(self) -> int: ...
    def weekday(self) -> int: ...
    def isocalendar(self) -> tuple[int, int, int]: ...


def format_offset(offset: _dt.timedelta | None, separator: str) -> str:
    """Format a UTC offset as ``+HHMM[SS[.ffffff]]`` (``separator`` between fields).

    Args:
        offset: The UTC offset, or ``None`` for naive values.
        separator: ``""`` for ``%z`` or ``":"`` for ``%:z``.

    Returns:
        The formatted offset, or ``""`` if ``offset`` is ``None``.
    """
    if offset is None:
        return ""
    sign = "+"
    if offset < _dt.timedelta(0):
        sign, offset = "-", -offset
    hours, rest = divmod(offset, _dt.timedelta(hours=1))
    minutes, rest = divmod(rest, _dt.timedelta(minutes=1))
    seconds = rest.seconds
    text = f"{sign}{hours:02d}{separator}{minutes:02d}"
    if seconds or rest.microseconds:
        text += f"{separator}{seconds:02d}"
        if rest.microseconds:
            text += f".{rest.microseconds:06d}"
    return text


def _day_of_year(value: _DateLike) -> int:
    return _lookup.days_before_month(value.year, value.month) + value.day


def _week_number(value: _DateLike, *, monday_first: bool) -> int:
    day_index = _day_of_year(value) - 1
    weekday = value.weekday() if monday_first else (value.weekday() + 1) % 7
    return (day_index + 7 - weekday) // 7


def _hour(value: object) -> int:
    hour: int = getattr(value, "hour", 0)
    return hour


def _utcoffset(value: object) -> _dt.timedelta | None:
    method: Callable[[], _dt.timedelta | None] | None = getattr(value, "utcoffset", None)
    return method() if method is not None else None


def _tzname(value: object) -> str:
    method: Callable[[], str | None] | None = getattr(value, "tzname", None)
    name = method() if method is not None else None
    return name or ""


def _render(value: _DateLike, code: str, locale: Locale) -> str:
    match code:
        case "a":
            return locale.weekday_abbrs[value.weekday()]
        case "A":
            return locale.weekday_names[value.weekday()]
        case "b" | "h":
            return locale.month_abbrs[value.month - 1]
        case "B":
            return locale.month_names[value.month - 1]
        case "C":
            return f"{value.year // 100:02d}"
        case "d":
            return f"{value.day:02d}"
        case "e":
            return f"{value.day:2d}"
        case "f":
            return f"{getattr(value, 'microsecond', 0):06d}"
        case "G":
            return f"{value.isocalendar()[0]:04d}"
        case "H":
            return f"{_hour(value):02d}"
        case "I":
            return f"{(_hour(value) % _NOON) or _NOON:02d}"
        case "j":
            return f"{_day_of_year(value):03d}"
        case "m":
            return f"{value.month:02d}"
        case "M":
            return f"{getattr(value, 'minute', 0):02d}"
        case "p":
            return locale.am_pm[0 if _hour(value) < _NOON else 1]
        case "S":
            return f"{getattr(value, 'second', 0):02d}"
        case "u":
            return f"{value.weekday() + 1}"
        case "U":
            return f"{_week_number(value, monday_first=False):02d}"
        case "V":
            return f"{value.isocalendar()[1]:02d}"
        case "w":
            return f"{(value.weekday() + 1) % 7}"
        case "W":
            return f"{_week_number(value, monday_first=True):02d}"
        case "y":
            return f"{value.year % 100:02d}"
        case "Y":
            return f"{value.year:04d}"
        case "z":
            return format_offset(_utcoffset(value), "")
        case ":z":
            return format_offset(_utcoffset(value), ":")
        case "Z":
            return _tzname(value)
        case "%":
            return "%"
        case "n":
            return "\n"
        case "t":
            return "\t"
        case "c":
            return strftime(value, locale.datetime_format, locale)
        case "x":
            return strftime(value, locale.date_format, locale)
        case "X":
            return strftime(value, locale.time_format, locale)
        case _ if code in _COMPOSITES:
            return strftime(value, _COMPOSITES[code], locale)
        case _:
            message = f"invalid format directive '%{code}'"
            raise ValueError(message)


def strftime(value: _DateLike, fmt: str, locale: Locale) -> str:
    """Format a BS ``date`` or ``datetime`` according to ``fmt``.

    Args:
        value: A ``sambat.date`` or ``sambat.datetime``.
        fmt: The format string.
        locale: Names, digits and templates to use.

    Returns:
        The formatted string.

    Raises:
        TypeError: If ``fmt`` is not a string.
        ValueError: If ``fmt`` contains an unknown or incomplete directive.
    """
    if not isinstance(fmt, str):
        message = f"strftime() argument 1 must be str, not {type(fmt).__name__}"
        raise TypeError(message)
    pieces: list[str] = []
    index, length = 0, len(fmt)
    while index < length:
        char = fmt[index]
        index += 1
        if char != "%":
            pieces.append(char)
            continue
        if index >= length:
            message = "stray % at the end of the format string"
            raise ValueError(message)
        code = fmt[index]
        index += 1
        alternative_digits = False
        if code == "O":
            if index >= length or fmt[index] not in NUMERIC_DIRECTIVES:
                bad = fmt[index] if index < length else ""
                message = f"invalid format directive '%O{bad}'"
                raise ValueError(message)
            code = fmt[index]
            index += 1
            alternative_digits = True
        elif code == ":":
            if index >= length or fmt[index] != "z":
                message = "invalid format directive '%:' (only '%:z' is supported)"
                raise ValueError(message)
            code = ":z"
            index += 1
        text = _render(value, code, locale)
        if code in NUMERIC_DIRECTIVES:
            text = (
                text.translate(_TO_DEVANAGARI) if alternative_digits else locale.format_number(text)
            )
        pieces.append(text)
    return "".join(pieces)
