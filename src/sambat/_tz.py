"""The Asia/Kathmandu time zone, with its full offset history.

Nepal has never observed daylight saving time. Its UTC offset changed twice
(IANA tz database, zone ``Asia/Kathmandu``):

* local mean time, UTC+05:41:16, until 1920-01-01 00:00 local time;
* UTC+05:30 until 1986-01-01 00:00 local time;
* UTC+05:45 since.

The 1920 change set clocks back by 11 minutes 16 seconds, so wall times from
23:48:44 to 23:59:59 on 1919-12-31 happened twice (``fold`` selects which).
The 1986 change skipped wall times from 00:00 to 00:14:59 on 1986-01-01.
"""

from __future__ import annotations

import datetime as _dt

__all__ = ["NEPAL_TZ", "NepalTimeZone"]

_LMT = _dt.timedelta(hours=5, minutes=41, seconds=16)
_IST = _dt.timedelta(hours=5, minutes=30)
_NPT = _dt.timedelta(hours=5, minutes=45)
_ZERO = _dt.timedelta(0)

# Wall-clock boundaries (naive local times).
_LMT_END = _dt.datetime(1920, 1, 1)  # first wall time that is only valid in +05:30
_FOLD_1920_START = _LMT_END - (_LMT - _IST)  # 1919-12-31 23:48:44
_GAP_1986_START = _dt.datetime(1986, 1, 1)
_GAP_1986_END = _GAP_1986_START + (_NPT - _IST)  # 1986-01-01 00:15:00

# Transition instants in UTC (naive).
_UTC_1920 = _LMT_END - _LMT  # 1919-12-31 18:18:44 UTC
_UTC_1986 = _GAP_1986_START - _IST  # 1985-12-31 18:30:00 UTC


class NepalTimeZone(_dt.tzinfo):
    """``tzinfo`` for Nepal (IANA ``Asia/Kathmandu``), including historical offsets.

    The single instance is available as :data:`sambat.NEPAL_TZ`. It follows
    PEP 495 for the ambiguous and missing wall times created by the 1920 and
    1986 offset changes.

    Examples:
        >>> import datetime
        >>> from sambat import NEPAL_TZ
        >>> datetime.datetime(2026, 10, 1, 12, tzinfo=NEPAL_TZ).utcoffset()
        datetime.timedelta(seconds=20700)
        >>> datetime.datetime(1980, 1, 1, tzinfo=NEPAL_TZ).tzname()
        '+0530'
    """

    __slots__ = ()

    def utcoffset(self, dt: _dt.datetime | None) -> _dt.timedelta | None:
        """Return the UTC offset in force at local wall time ``dt``.

        Args:
            dt: A wall time whose ``tzinfo`` is this object, or ``None``.

        Returns:
            The offset, or ``None`` when ``dt`` is ``None``.
        """
        if dt is None:
            return None
        wall = dt.replace(tzinfo=None, fold=0)
        if wall < _FOLD_1920_START:
            return _LMT
        if wall < _LMT_END:
            return _IST if dt.fold else _LMT
        if wall < _GAP_1986_START:
            return _IST
        if wall < _GAP_1986_END:
            return _NPT if dt.fold else _IST
        return _NPT

    def dst(self, dt: _dt.datetime | None) -> _dt.timedelta | None:
        """Return the daylight saving adjustment, which is always zero.

        Args:
            dt: A wall time, or ``None``.

        Returns:
            ``timedelta(0)``, or ``None`` when ``dt`` is ``None``.
        """
        return None if dt is None else _ZERO

    def tzname(self, dt: _dt.datetime | None) -> str | None:
        """Return the tz database abbreviation for the offset in force.

        Args:
            dt: A wall time, or ``None``.

        Returns:
            ``"LMT"``, ``"+0530"`` or ``"+0545"``, or ``None`` when ``dt`` is ``None``.
        """
        offset = self.utcoffset(dt)
        if offset is None:
            return None
        if offset == _LMT:
            return "LMT"
        return "+0530" if offset == _IST else "+0545"

    def fromutc(self, dt: _dt.datetime) -> _dt.datetime:
        """Convert a UTC time (with ``tzinfo`` set to this object) to local time.

        Args:
            dt: A datetime whose fields are UTC and whose ``tzinfo`` is ``self``.

        Returns:
            The local wall time, with ``fold`` set for the repeated 1919 minutes.

        Raises:
            TypeError: If ``dt`` is not a ``datetime``.
            ValueError: If ``dt.tzinfo`` is not this object.
        """
        if not isinstance(dt, _dt.datetime):
            message = "fromutc() requires a datetime argument"
            raise TypeError(message)
        if dt.tzinfo is not self:
            message = "fromutc: dt.tzinfo is not self"
            raise ValueError(message)
        utc = dt.replace(tzinfo=None)
        if utc < _UTC_1920:
            return (utc + _LMT).replace(tzinfo=self, fold=0)
        if utc < _UTC_1986:
            local = utc + _IST
            fold = 1 if local < _LMT_END else 0
            return local.replace(tzinfo=self, fold=fold)
        return (utc + _NPT).replace(tzinfo=self, fold=0)

    def __repr__(self) -> str:
        return "sambat.NEPAL_TZ"

    def __str__(self) -> str:
        return "Asia/Kathmandu"

    def __reduce__(self) -> str:
        return "NEPAL_TZ"


NepalTimeZone.__module__ = "sambat"

NEPAL_TZ = NepalTimeZone()
"""The Asia/Kathmandu time zone (singleton :class:`NepalTimeZone` instance)."""
