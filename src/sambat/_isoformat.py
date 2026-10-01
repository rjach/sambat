"""ISO 8601 parsing for BS dates, following the grammar of Python 3.11+.

Date strings use the BS calendar; week dates use the BS week calendar described
in ``sambat._lookup.week1_monday``. Time strings are delegated to
``datetime.time.fromisoformat`` so they accept exactly what the running Python
accepts.
"""

from __future__ import annotations

import datetime as _dt

from sambat import _lookup

__all__ = ["parse_date", "parse_datetime"]

_EXTENDED_DATE = 10  # YYYY-MM-DD and YYYY-Www-D
_EXTENDED_WEEK = 8  # YYYY-Www
_BASIC_WEEK = 7  # YYYYWww
_BASIC_DATE = 8  # YYYYMMDD and YYYYWwwD


def _invalid(text: str) -> ValueError:
    return ValueError(f"Invalid isoformat string: {text!r}")


def _digits(text: str, original: str) -> int:
    if not (text.isascii() and text.isdigit()):
        raise _invalid(original)
    return int(text)


def parse_date(text: str) -> tuple[int, int, int]:
    """Parse an ISO 8601 BS date string.

    Accepted forms: ``YYYY-MM-DD``, ``YYYYMMDD``, ``YYYY-Www``, ``YYYY-Www-D``,
    ``YYYYWww`` and ``YYYYWwwD``.

    Args:
        text: The date string.

    Returns:
        The BS ``(year, month, day)``.

    Raises:
        ValueError: If the string is malformed or the date is invalid.
    """
    length = len(text)
    if length < _BASIC_WEEK or not text[:4].isascii() or not text[:4].isdigit():
        raise _invalid(text)
    year = int(text[:4])
    extended = text[4] == "-"
    body = text[5:] if extended else text[4:]
    try:
        if body.startswith("W"):
            week_digits = body[1:3]
            rest = body[3:]
            if extended and rest:
                if not rest.startswith("-"):
                    raise _invalid(text)
                rest = rest[1:]
            week = _digits(week_digits, text)
            if len(week_digits) != 2 or len(rest) > 1:
                raise _invalid(text)
            weekday = _digits(rest, text) if rest else 1
            ordinal = _lookup.week_to_ordinal(year, week, weekday)
            return _lookup.ordinal_to_ymd(ordinal)
        if extended:
            if length != _EXTENDED_DATE or text[7] != "-":
                raise _invalid(text)
            month, day = _digits(text[5:7], text), _digits(text[8:10], text)
        else:
            if length != _BASIC_DATE:
                raise _invalid(text)
            month, day = _digits(text[4:6], text), _digits(text[6:8], text)
        _lookup.check_day(year, month, day)
    except ValueError as exc:
        if str(exc).startswith("Invalid isoformat"):
            raise
        message = f"Invalid isoformat string: {text!r} ({exc})"
        raise ValueError(message) from exc
    return year, month, day


def _date_length(text: str) -> int:
    """Return the length of the date component of an ISO datetime string."""
    length = len(text)
    if length <= _BASIC_WEEK:
        return length
    if text[4] == "-":
        if text[5] != "W":
            return _EXTENDED_DATE
        if length > _EXTENDED_WEEK and text[8] == "-":
            # YYYY-Www-D; a digit after it means the hyphen was the separator.
            if length > _EXTENDED_DATE and text[10].isdigit():
                return _EXTENDED_WEEK
            return _EXTENDED_DATE
        return _EXTENDED_WEEK
    if text[4] == "W":
        end = _BASIC_WEEK
        while end < length and text[end].isascii() and text[end].isdigit():
            end += 1
        if end < 9:
            return end
        return _BASIC_WEEK if end % 2 == 0 else _BASIC_DATE
    return _BASIC_DATE


def parse_datetime(text: str) -> tuple[tuple[int, int, int], _dt.time | None]:
    """Split and parse an ISO 8601 BS datetime string.

    Args:
        text: The datetime string; the separator may be any single character.

    Returns:
        The BS ``(year, month, day)`` and the parsed time (``None`` when the
        string has no time component).

    Raises:
        ValueError: If the string is malformed.
    """
    if len(text) < _BASIC_WEEK:
        raise _invalid(text)
    split = _date_length(text)
    date_part = text[:split]
    time_part = text[split + 1 :]
    if split < len(text) and not time_part:
        raise _invalid(text)
    ymd = parse_date(date_part)
    if split >= len(text):
        return ymd, None
    try:
        parsed_time = _dt.time.fromisoformat(time_part)
    except ValueError as exc:
        raise _invalid(text) from exc
    return ymd, parsed_time
