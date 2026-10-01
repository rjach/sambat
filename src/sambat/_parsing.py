"""Pure-Python ``strptime`` for Bikram Sambat dates.

Numbers may be written with ASCII or Devanagari digits. Month and weekday names
come from the given :class:`~sambat.locale.Locale` (plus its documented
alternative spellings) and are matched case-insensitively.
"""

from __future__ import annotations

import datetime as _dt
import re
import warnings
from functools import lru_cache
from typing import TYPE_CHECKING, NamedTuple

from sambat import _lookup
from sambat.text import to_ascii_digits

if TYPE_CHECKING:
    from sambat.locale import Locale

__all__ = ["ParsedFields", "strptime"]

_D = "[0-9०-९]"
_DEFAULT_YEAR = 2000
_NOON = 12
_COMPOSITES = {"D": "%m/%d/%y", "F": "%Y-%m-%d", "r": "%I:%M:%S %p", "R": "%H:%M", "T": "%H:%M:%S"}
_NUMERIC_PATTERNS = {
    "d": rf"(?P<d>{_D}{{1,2}})",
    "e": rf"(?P<d> ?{_D}{{1,2}})",
    "f": rf"(?P<f>{_D}{{1,6}})",
    "G": rf"(?P<G>{_D}{{4}})",
    "H": rf"(?P<H>{_D}{{1,2}})",
    "I": rf"(?P<I>{_D}{{1,2}})",
    "j": rf"(?P<j>{_D}{{1,3}})",
    "m": rf"(?P<m>{_D}{{1,2}})",
    "M": rf"(?P<M>{_D}{{1,2}})",
    "S": rf"(?P<S>{_D}{{1,2}})",
    "u": r"(?P<u>[1-7१-७])",
    "U": rf"(?P<U>{_D}{{1,2}})",
    "V": rf"(?P<V>{_D}{{1,2}})",
    "w": r"(?P<w>[0-6०-६])",
    "W": rf"(?P<W>{_D}{{1,2}})",
    "y": rf"(?P<y>{_D}{{2}})",
    "Y": rf"(?P<Y>{_D}{{4}})",
}
_OFFSET = r"(?P<z>[+-]\d\d:?[0-5]\d(?::?[0-5]\d(?:\.\d{1,6})?)?|(?-i:Z))"
_TZNAME = r"(?P<Z>UTC|GMT|LMT|NPT|\+0530|\+0545)"


class ParsedFields(NamedTuple):
    """Fields extracted by :func:`strptime`."""

    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    microsecond: int
    tzinfo: _dt.tzinfo | None


def _alternation(group: str, spellings: list[tuple[str, int]]) -> str:
    ordered = sorted(spellings, key=lambda item: len(item[0]), reverse=True)
    return f"(?P<{group}>" + "|".join(re.escape(text) for text, _ in ordered) + ")"


def _lookup_table(spellings: list[tuple[str, int]]) -> dict[str, int]:
    return {text.casefold(): value for text, value in spellings}


class _Compiled(NamedTuple):
    regex: re.Pattern[str]
    months: dict[str, int]
    weekdays: dict[str, int]
    am_pm: dict[str, int]


def _expand(fmt: str, locale: Locale) -> str:
    """Expand composite directives (``%c``, ``%D``, ...) recursively."""
    templates = {"c": locale.datetime_format, "x": locale.date_format, "X": locale.time_format}
    templates.update(_COMPOSITES)
    pieces: list[str] = []
    index = 0
    while index < len(fmt):
        char = fmt[index]
        if char == "%" and index + 1 < len(fmt) and fmt[index + 1] in templates:
            pieces.append(_expand(templates[fmt[index + 1]], locale))
            index += 2
            continue
        if char == "%" and index + 1 < len(fmt):
            pieces.append(fmt[index : index + 2])
            index += 2
            continue
        pieces.append(char)
        index += 1
    return "".join(pieces)


@lru_cache(maxsize=128)
def _compile(fmt: str, locale: Locale) -> _Compiled:
    months = [(text, month) for month in range(1, 13) for text in locale.month_spellings(month)]
    weekdays = [(text, day) for day in range(7) for text in locale.weekday_spellings(day)]
    am_pm = [(locale.am_pm[0], 0), (locale.am_pm[1], 1)]
    named = {
        "a": _alternation("a", weekdays),
        "b": _alternation("b", months),
        "p": _alternation("p", am_pm),
        "z": _OFFSET,
        ":z": _OFFSET,
        "Z": _TZNAME,
    }
    named["A"] = named["a"]
    named["B"] = named["h"] = named["b"]

    expanded = _expand(fmt, locale)
    pattern: list[str] = []
    seen: set[str] = set()
    index = 0
    while index < len(expanded):
        char = expanded[index]
        index += 1
        if char != "%":
            pattern.append(r"\s+" if char.isspace() else re.escape(char))
            continue
        if index >= len(expanded):
            message = "stray % at the end of the format string"
            raise ValueError(message)
        code = expanded[index]
        index += 1
        if code == "O" and index < len(expanded) and expanded[index] in _NUMERIC_PATTERNS:
            code = expanded[index]
            index += 1
        elif code == ":" and index < len(expanded) and expanded[index] == "z":
            code = ":z"
            index += 1
        if code == "%":
            pattern.append("%")
            continue
        if code in {"n", "t"}:
            pattern.append(r"\s+")
            continue
        regex = _NUMERIC_PATTERNS.get(code) or named.get(code)
        if regex is None:
            message = f"invalid format directive '%{code}'"
            raise ValueError(message)
        group = regex[4 : regex.index(">")]
        if group in seen:
            message = f"redefinition of group name {group!r} (directive '%{code}' is repeated)"
            raise ValueError(message)
        seen.add(group)
        pattern.append(regex)
    return _Compiled(
        regex=re.compile("".join(pattern), re.IGNORECASE),
        months=_lookup_table(months),
        weekdays=_lookup_table(weekdays),
        am_pm=_lookup_table(am_pm),
    )


def _parse_offset(text: str, tzname: str | None) -> _dt.tzinfo:
    if text == "Z":
        offset = _dt.timedelta(0)
    else:
        sign = -1 if text[0] == "-" else 1
        body = text[1:].replace(":", "")
        hours, minutes = int(body[0:2]), int(body[2:4])
        seconds = int(body[4:6]) if len(body) >= 6 else 0
        fraction = body[7:] if len(body) > 6 else ""
        microseconds = int(fraction.ljust(6, "0")) if fraction else 0
        offset = sign * _dt.timedelta(
            hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds
        )
    return _dt.timezone(offset, tzname) if tzname else _dt.timezone(offset)


def _julian_from_week(year: int, week: int, weekday: int, *, monday_first: bool) -> int:
    """Return the 1-based day of year for a ``%U``/``%W`` week and ``weekday`` (Monday = 0)."""
    first_weekday = (_lookup.year_start_ordinal(year) + 6) % 7
    if not monday_first:
        first_weekday = (first_weekday + 1) % 7
        weekday = (weekday + 1) % 7
    week_0_length = (7 - first_weekday) % 7
    if week == 0:
        return 1 + weekday - first_weekday
    return 1 + week_0_length + 7 * (week - 1) + weekday


def strptime(text: str, fmt: str, locale: Locale) -> ParsedFields:
    """Parse ``text`` according to ``fmt``.

    Args:
        text: The string to parse.
        fmt: The format string (same directives as ``strftime``).
        locale: The locale whose names are accepted.

    Returns:
        The parsed fields.

    Raises:
        TypeError: If ``text`` or ``fmt`` is not a string.
        ValueError: If the text does not match or describes an invalid date.
    """
    for name, value in (("date_string", text), ("format", fmt)):
        if not isinstance(value, str):
            message = f"strptime() argument {name!r} must be str, not {type(value).__name__}"
            raise TypeError(message)
    compiled = _compile(fmt, locale)
    found = compiled.regex.match(text)
    if found is None:
        message = f"time data {text!r} does not match format {fmt!r}"
        raise ValueError(message)
    if found.end() != len(text):
        message = f"unconverted data remains: {text[found.end() :]}"
        raise ValueError(message)
    groups = {key: value for key, value in found.groupdict().items() if value is not None}
    numbers = {
        key: int(to_ascii_digits(value.strip()))
        for key, value in groups.items()
        if key in _NUMERIC_PATTERNS
    }

    weekday: int | None = None
    if "a" in groups:
        weekday = compiled.weekdays[groups["a"].casefold()]
    elif "u" in numbers:
        weekday = numbers["u"] - 1
    elif "w" in numbers:
        weekday = (numbers["w"] - 1) % 7

    if "Y" in numbers:
        year = numbers["Y"]
    elif "y" in numbers:
        year = _DEFAULT_YEAR + numbers["y"]
    else:
        year = _DEFAULT_YEAR
        if "d" in numbers and "G" not in numbers:
            warnings.warn(
                "Parsing a day of month without a year is ambiguous because BS month "
                "lengths depend on the year; sambat assumes BS 2000. Add a year (%Y) "
                "to the format.",
                DeprecationWarning,
                stacklevel=4,
            )
    month = compiled.months[groups["b"].casefold()] if "b" in groups else numbers.get("m", 1)
    day = numbers.get("d", 1)

    if "G" in numbers or "V" in numbers:
        if not {"G", "V"} <= numbers.keys() or weekday is None:
            message = "ISO week directive '%V' requires '%G' and a weekday directive ('%u', '%a')"
            raise ValueError(message)
        ordinal = _lookup.week_to_ordinal(numbers["G"], numbers["V"], weekday + 1)
        year, month, day = _lookup.ordinal_to_ymd(ordinal)
    elif "j" in numbers or (weekday is not None and ("U" in numbers or "W" in numbers)):
        if "j" in numbers:
            julian = numbers["j"]
        else:
            monday_first = "W" in numbers
            week = numbers["W"] if monday_first else numbers["U"]
            assert weekday is not None  # noqa: S101 - narrowed by the elif condition
            julian = _julian_from_week(year, week, weekday, monday_first=monday_first)
        if not 1 <= julian <= _lookup.days_in_year(year):
            message = f"day of year {julian} is out of range for BS {year}"
            raise ValueError(message)
        year, month, day = _lookup.ordinal_to_ymd(_lookup.year_start_ordinal(year) + julian - 1)

    hour = numbers.get("H", 0)
    if "I" in numbers:
        hour = numbers["I"] % _NOON
        if "p" in groups and compiled.am_pm[groups["p"].casefold()] == 1:
            hour += _NOON
    microsecond = int(to_ascii_digits(groups["f"]).ljust(6, "0")) if "f" in groups else 0
    tzinfo = _parse_offset(groups["z"], groups.get("Z")) if "z" in groups else None

    _lookup.check_day(year, month, day)
    return ParsedFields(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=numbers.get("M", 0),
        second=numbers.get("S", 0),
        microsecond=microsecond,
        tzinfo=tzinfo,
    )
