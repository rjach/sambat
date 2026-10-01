"""Integer-only Bikram Sambat calendar arithmetic over the verified month table.

Every function here works on plain integers: BS ``(year, month, day)`` triples
and proleptic Gregorian ordinals (the numbers returned by
``datetime.date.toordinal``). Nothing in this module knows about the public
``date``/``datetime`` classes.
"""

from __future__ import annotations

from bisect import bisect_right
from itertools import accumulate

from sambat._table import FIRST_YEAR, MONTH_LENGTHS, YEAR_START_ORDINALS

MINYEAR: int = FIRST_YEAR
"""The first BS year included in the verified calendar table."""

MAXYEAR: int = FIRST_YEAR + len(MONTH_LENGTHS) - 1
"""The last BS year included in the verified calendar table."""

MIN_ORDINAL: int = YEAR_START_ORDINALS[0]
"""Gregorian ordinal of ``MINYEAR``-01-01 (BS)."""

MAX_ORDINAL: int = YEAR_START_ORDINALS[-1] - 1
"""Gregorian ordinal of the last day of ``MAXYEAR`` (BS)."""

MONTHS_PER_YEAR = 12

# _MONTH_OFFSETS[i][m] = days in year (FIRST_YEAR + i) before month m + 1.
_MONTH_OFFSETS: tuple[tuple[int, ...], ...] = tuple(
    (0, *accumulate(lengths)) for lengths in MONTH_LENGTHS
)


def year_range_message(year: int) -> str:
    """Explain why ``year`` is outside the supported range.

    Args:
        year: The rejected BS year.

    Returns:
        A human-readable error message.
    """
    base = f"year {year} is out of range; sambat supports BS {MINYEAR}..{MAXYEAR}"
    if year > MAXYEAR:
        return (
            f"{base} (later years had no officially published calendar when this "
            f"version of sambat was released; upgrading sambat may add them)"
        )
    return f"{base} (earlier years are not in the verified calendar table)"


def check_year(year: int) -> None:
    """Raise ``ValueError`` if ``year`` is outside the supported range.

    Args:
        year: A BS year.

    Raises:
        ValueError: If the year is not covered by the calendar table.
    """
    if not MINYEAR <= year <= MAXYEAR:
        raise ValueError(year_range_message(year))


def check_month(month: int) -> None:
    """Raise ``ValueError`` if ``month`` is not in 1..12.

    Args:
        month: A BS month number.

    Raises:
        ValueError: If the month is not in 1..12.
    """
    if not 1 <= month <= MONTHS_PER_YEAR:
        message = f"month must be in 1..12, not {month}"
        raise ValueError(message)


def days_in_month(year: int, month: int) -> int:
    """Return the number of days (29..32) in a BS month.

    Args:
        year: A supported BS year.
        month: A month number in 1..12.

    Returns:
        The month length.

    Raises:
        ValueError: If the year or month is out of range.
    """
    check_year(year)
    check_month(month)
    return MONTH_LENGTHS[year - FIRST_YEAR][month - 1]


def days_in_year(year: int) -> int:
    """Return the number of days (365 or 366) in a BS year.

    Args:
        year: A supported BS year.

    Returns:
        The year length.

    Raises:
        ValueError: If the year is out of range.
    """
    check_year(year)
    return _MONTH_OFFSETS[year - FIRST_YEAR][MONTHS_PER_YEAR]


def days_before_month(year: int, month: int) -> int:
    """Return the number of days in ``year`` before the first day of ``month``.

    Args:
        year: A supported BS year.
        month: A month number in 1..12.

    Returns:
        A day count in 0..334.
    """
    check_year(year)
    check_month(month)
    return _MONTH_OFFSETS[year - FIRST_YEAR][month - 1]


def year_start_ordinal(year: int) -> int:
    """Return the Gregorian ordinal of Baisakh 1 of ``year``.

    ``MAXYEAR + 1`` is accepted and returns the ordinal of the day after the
    last supported day, which is known exactly from the table.

    Args:
        year: A BS year in ``MINYEAR..MAXYEAR + 1``.

    Returns:
        A proleptic Gregorian ordinal.

    Raises:
        ValueError: If the year is outside ``MINYEAR..MAXYEAR + 1``.
    """
    if year == MAXYEAR + 1:
        return YEAR_START_ORDINALS[-1]
    check_year(year)
    return YEAR_START_ORDINALS[year - FIRST_YEAR]


def check_day(year: int, month: int, day: int) -> None:
    """Raise ``ValueError`` if ``(year, month, day)`` is not a valid BS date.

    Args:
        year: A BS year.
        month: A BS month.
        day: A day of the month.

    Raises:
        ValueError: If any field is out of range.
    """
    length = days_in_month(year, month)
    if not 1 <= day <= length:
        message = f"day must be in 1..{length} for BS {year}-{month:02d}, not {day}"
        raise ValueError(message)


def ymd_to_ordinal(year: int, month: int, day: int) -> int:
    """Convert a BS date to a proleptic Gregorian ordinal.

    Args:
        year: A BS year.
        month: A BS month.
        day: A day of the month.

    Returns:
        The ordinal shared with ``datetime.date.toordinal``.

    Raises:
        ValueError: If the date is invalid or out of range.
    """
    check_day(year, month, day)
    index = year - FIRST_YEAR
    return YEAR_START_ORDINALS[index] + _MONTH_OFFSETS[index][month - 1] + day - 1


def ordinal_to_ymd(ordinal: int) -> tuple[int, int, int]:
    """Convert a proleptic Gregorian ordinal to a BS ``(year, month, day)``.

    Args:
        ordinal: A day number as returned by ``datetime.date.toordinal``.

    Returns:
        The BS year, month and day.

    Raises:
        ValueError: If the ordinal falls outside the supported range.
    """
    if not MIN_ORDINAL <= ordinal <= MAX_ORDINAL:
        message = (
            f"ordinal {ordinal} is out of range; sambat supports ordinals "
            f"{MIN_ORDINAL}..{MAX_ORDINAL} (BS {MINYEAR}..{MAXYEAR})"
        )
        raise ValueError(message)
    index = bisect_right(YEAR_START_ORDINALS, ordinal) - 1
    day_of_year = ordinal - YEAR_START_ORDINALS[index]
    offsets = _MONTH_OFFSETS[index]
    month = bisect_right(offsets, day_of_year, 0, MONTHS_PER_YEAR)
    return FIRST_YEAR + index, month, day_of_year - offsets[month - 1] + 1


def week1_monday(year: int) -> int:
    """Return the ordinal of the Monday that starts week 1 of a BS week-year.

    Week 1 is the Monday-to-Sunday week that contains the first Thursday of
    the BS year, mirroring the ISO 8601 rule for Gregorian years.

    Args:
        year: A BS year in ``MINYEAR..MAXYEAR + 1``.

    Returns:
        A proleptic Gregorian ordinal.
    """
    first = year_start_ordinal(year)
    first_weekday = (first + 6) % 7  # Monday == 0, as date.weekday()
    monday = first - first_weekday
    if first_weekday > 3:  # the year starts after Thursday
        monday += 7
    return monday


def ordinal_to_week(ordinal: int) -> tuple[int, int, int]:
    """Return the BS ``(week_year, week, weekday)`` of an ordinal.

    Args:
        ordinal: A supported proleptic Gregorian ordinal.

    Returns:
        The week-numbering year, the week (1..53) and the ISO weekday (1..7).

    Raises:
        ValueError: If the week-year cannot be determined because it would
            start before ``MINYEAR``.
    """
    year = ordinal_to_ymd(ordinal)[0]
    week, day = divmod(ordinal - week1_monday(year), 7)
    if week < 0:
        year -= 1
        if year < MINYEAR:
            message = (
                f"the BS week number of ordinal {ordinal} falls in BS {year}, "
                f"which is outside the supported range"
            )
            raise ValueError(message)
        week, day = divmod(ordinal - week1_monday(year), 7)
    elif week >= 52 and ordinal >= week1_monday(year + 1):
        year += 1
        week = 0
    return year, week + 1, day + 1


def week_to_ordinal(year: int, week: int, weekday: int) -> int:
    """Return the ordinal of a BS ``(week_year, week, weekday)`` triple.

    Args:
        year: A BS week-numbering year.
        week: A week number (1..53).
        weekday: An ISO weekday (1 = Monday .. 7 = Sunday).

    Returns:
        A proleptic Gregorian ordinal.

    Raises:
        ValueError: If any field is invalid or the result is out of range.
    """
    if not 1 <= weekday <= 7:
        message = f"Invalid weekday: {weekday} (range is [1, 7])"
        raise ValueError(message)
    if not MINYEAR <= year <= MAXYEAR + 1:
        raise ValueError(year_range_message(year))
    if not 1 <= week <= 53:
        message = f"Invalid week: {week}"
        raise ValueError(message)
    if week == 53 and year <= MAXYEAR and week1_monday(year + 1) - week1_monday(year) < 53 * 7:
        message = f"Invalid week: {week} (BS {year} has 52 weeks)"
        raise ValueError(message)
    ordinal = week1_monday(year) + (week - 1) * 7 + weekday - 1
    if not in_range(ordinal):
        message = f"week {week} of BS week-year {year} is outside the supported range"
        raise ValueError(message)
    return ordinal


def in_range(ordinal: int) -> bool:
    """Return whether ``ordinal`` falls inside the supported range.

    Args:
        ordinal: A proleptic Gregorian ordinal.

    Returns:
        ``True`` if a BS date exists for the ordinal.
    """
    return MIN_ORDINAL <= ordinal <= MAX_ORDINAL
