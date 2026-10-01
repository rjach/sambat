"""Exact Bikram Sambat (Nepali calendar) dates with the full ``datetime`` API.

``sambat.date`` and ``sambat.datetime`` mirror :class:`datetime.date` and
:class:`datetime.datetime`, with year, month and day in the Bikram Sambat (BS)
calendar. The calendar-independent types (``timedelta``, ``time``, ``tzinfo``,
``timezone`` and ``UTC``) are the standard library's own objects.

Month lengths come from a table of officially published BS years; dates
outside :data:`MINYEAR`..:data:`MAXYEAR` raise ``ValueError`` instead of being
guessed.

Examples:
    >>> import sambat
    >>> d = sambat.date(2083, 1, 1)
    >>> d.to_gregorian()
    datetime.date(2026, 4, 14)
    >>> d + sambat.timedelta(days=31)
    sambat.date(2083, 2, 1)
    >>> sambat.timedelta is __import__("datetime").timedelta
    True
"""

from __future__ import annotations

import datetime as _dt
from importlib import import_module
from typing import TYPE_CHECKING, Any

from sambat._date import IsoCalendarDate, date
from sambat._datetime import datetime
from sambat._lookup import MAXYEAR, MINYEAR
from sambat._tz import NEPAL_TZ, NepalTimeZone

if TYPE_CHECKING:
    from types import ModuleType

try:
    from sambat._version import __version__
except ImportError:  # pragma: no cover - only when running from a source tree without a build
    __version__ = "0.0.0+unknown"

__all__ = [
    "MAXYEAR",
    "MINYEAR",
    "NEPAL_TZ",
    "UTC",
    "IsoCalendarDate",
    "NepalTimeZone",
    "__version__",
    "date",
    "datetime",
    "now_np",
    "time",
    "timedelta",
    "timezone",
    "today_np",
    "tzinfo",
]

time = _dt.time
timedelta = _dt.timedelta
timezone = _dt.timezone
tzinfo = _dt.tzinfo
UTC = _dt.UTC

_SUBMODULES = frozenset({"calendar", "compat", "delta", "fiscal", "locale", "periods", "text"})


def today_np() -> date:
    """Return today's BS date in Nepal, whatever the machine's time zone.

    Returns:
        The current date in ``Asia/Kathmandu``.
    """
    return datetime.now(NEPAL_TZ).date()


def now_np() -> datetime:
    """Return the current aware BS datetime in Nepal time (``Asia/Kathmandu``).

    Returns:
        The current datetime with ``tzinfo=NEPAL_TZ``.
    """
    return datetime.now(NEPAL_TZ)


def __getattr__(name: str) -> ModuleType | Any:
    """Import public submodules lazily (``sambat.fiscal`` works without an import)."""
    if name in _SUBMODULES:
        return import_module(f"sambat.{name}")
    message = f"module 'sambat' has no attribute {name!r}"
    raise AttributeError(message)


def __dir__() -> list[str]:
    return sorted({*__all__, *_SUBMODULES})
