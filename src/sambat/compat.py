"""Helpers for migrating from the ``nepali-datetime`` package.

The conversion functions are deprecated aliases kept for two minor releases;
new code should use :meth:`sambat.date.from_gregorian` and
:meth:`sambat.date.to_gregorian`.

:func:`translate_format` rewrites nepali-datetime format strings, whose custom
letters (``%K``, ``%N``, ``%G``, ...) collide with standard ``strftime``
directives, into sambat's ``locale=`` + ``%O`` equivalents.

Examples:
    >>> from sambat import date
    >>> from sambat.compat import translate_format
    >>> fmt, locale = translate_format("%K-%n-%D %N")
    >>> fmt
    '%OY-%Om-%Od %B'
    >>> date(2083, 6, 15).strftime(fmt, locale=locale)
    '२०८३-०६-१५ असोज'
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import warnings

from sambat._date import date
from sambat._datetime import datetime
from sambat.locale import ASCII_DIGITS, EN, NE, Locale

__all__ = [
    "from_datetime_date",
    "from_datetime_datetime",
    "to_datetime_date",
    "to_datetime_datetime",
    "translate_format",
]

# nepali-datetime directive -> (sambat directive, needs Nepali names)
_DIRECTIVES: dict[str, tuple[str, bool]] = {
    "a": ("%a", False),
    "A": ("%A", False),
    "b": ("%b", False),
    "B": ("%B", False),
    "d": ("%d", False),
    "H": ("%H", False),
    "I": ("%I", False),
    "m": ("%m", False),
    "M": ("%M", False),
    "p": ("%p", False),
    "S": ("%S", False),
    "U": ("%U", False),
    "w": ("%w", False),
    "y": ("%y", False),
    "Y": ("%Y", False),
    "%": ("%%", False),
    "D": ("%Od", False),  # Devanagari day
    "n": ("%Om", False),  # Devanagari month
    "k": ("%Oy", False),  # Devanagari 2-digit year
    "K": ("%OY", False),  # Devanagari year
    "h": ("%OH", False),  # Devanagari hour
    "i": ("%OI", False),  # Devanagari 12-hour
    "l": ("%OM", False),  # Devanagari minute
    "s": ("%OS", False),  # Devanagari second
    "G": ("%A", True),  # Nepali weekday name
    "N": ("%B", True),  # Nepali month name
}
_ENGLISH_NAMES = frozenset("aAbBp")


def _deprecated(old: str, new: str) -> None:
    warnings.warn(
        f"sambat.compat.{old}() is deprecated; use {new} instead",
        DeprecationWarning,
        stacklevel=3,
    )


def from_datetime_date(value: _dt.date) -> date:
    """Deprecated alias of :meth:`sambat.date.from_gregorian`."""
    _deprecated("from_datetime_date", "sambat.date.from_gregorian()")
    return date.from_gregorian(value)


def to_datetime_date(value: date) -> _dt.date:
    """Deprecated alias of :meth:`sambat.date.to_gregorian`."""
    _deprecated("to_datetime_date", "sambat.date.to_gregorian()")
    return date.to_gregorian(value)


def from_datetime_datetime(value: _dt.datetime) -> datetime:
    """Deprecated alias of :meth:`sambat.datetime.from_gregorian`."""
    _deprecated("from_datetime_datetime", "sambat.datetime.from_gregorian()")
    return datetime.from_gregorian(value)


def to_datetime_datetime(value: datetime) -> _dt.datetime:
    """Deprecated alias of :meth:`sambat.datetime.to_gregorian`."""
    _deprecated("to_datetime_datetime", "sambat.datetime.to_gregorian()")
    return value.to_gregorian()


def translate_format(old_format: str) -> tuple[str, Locale]:
    """Translate a nepali-datetime format string to a sambat one.

    Args:
        old_format: A format string written for nepali-datetime.

    Returns:
        ``(new_format, locale)`` to pass to ``strftime(new_format, locale=locale)``.
        The locale is Nepali (with ASCII digits for plain numeric directives)
        when the old format used Nepali names, otherwise English.

    Raises:
        ValueError: If the format uses an unsupported directive, or mixes
            English and Nepali names (split it into two calls instead).
    """
    pieces: list[str] = []
    nepali_names = english_names = False
    index = 0
    while index < len(old_format):
        char = old_format[index]
        index += 1
        if char != "%":
            pieces.append(char)
            continue
        if index >= len(old_format):
            message = "stray % at the end of the format string"
            raise ValueError(message)
        code = old_format[index]
        index += 1
        if code not in _DIRECTIVES:
            message = f"nepali-datetime directive '%{code}' has no sambat equivalent"
            raise ValueError(message)
        replacement, nepali = _DIRECTIVES[code]
        nepali_names |= nepali
        english_names |= code in _ENGLISH_NAMES
        pieces.append(replacement)
    if nepali_names and english_names:
        message = "the format mixes English and Nepali names; translate the parts separately"
        raise ValueError(message)
    locale = dataclasses.replace(NE, digits=ASCII_DIGITS) if nepali_names else EN
    return "".join(pieces), locale
