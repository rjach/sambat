"""Bikram Sambat counterpart of the standard library :mod:`calendar` module.

The functions and classes mirror :mod:`calendar` (``monthrange``,
``monthcalendar``, ``Calendar``, ``TextCalendar``, ``HTMLCalendar``, ...) with
months in the BS calendar. Weeks start on Monday by default, as in the
standard library; pass ``firstweekday=SUNDAY`` for the Nepali convention.

:class:`DualTextCalendar` and :class:`DualHTMLCalendar` render a month the
way printed Nepali wall calendars do: each BS day shows the Gregorian day
number beside it.

Examples:
    >>> from sambat import calendar
    >>> calendar.monthrange(2083, 6)  # (weekday of day 1, number of days)
    (3, 31)
    >>> calendar.isleap(2081), calendar.days_in_year(2081)
    (True, 366)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import sys
import unicodedata
from enum import IntEnum
from itertools import repeat
from typing import TYPE_CHECKING, TypeVar

from sambat import _lookup
from sambat._date import date
from sambat.locale import EN, Locale, get_locale

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence

__all__ = [
    "ASAR",
    "ASHWIN",
    "BAISHAKH",
    "BHADRA",
    "CHAITRA",
    "FALGUN",
    "FRIDAY",
    "JESTHA",
    "KARTIK",
    "MAGH",
    "MANGSIR",
    "MONDAY",
    "POUSH",
    "SATURDAY",
    "SHRAWAN",
    "SUNDAY",
    "THURSDAY",
    "TUESDAY",
    "WEDNESDAY",
    "Calendar",
    "Day",
    "DualHTMLCalendar",
    "DualTextCalendar",
    "HTMLCalendar",
    "IllegalMonthError",
    "IllegalWeekdayError",
    "LocaleHTMLCalendar",
    "LocaleTextCalendar",
    "Month",
    "TextCalendar",
    "calendar",
    "day_abbr",
    "day_name",
    "days_in_month",
    "days_in_year",
    "error",
    "firstweekday",
    "format",
    "formatstring",
    "isleap",
    "leapdays",
    "main",
    "month",
    "month_abbr",
    "month_name",
    "monthcalendar",
    "monthrange",
    "prcal",
    "prmonth",
    "prweek",
    "setfirstweekday",
    "standalone_month_abbr",
    "standalone_month_name",
    "supported_range",
    "timegm",
    "week",
    "weekday",
    "weekheader",
]

_T = TypeVar("_T")
_MONTHS = 12
_DAYS_PER_WEEK = 7
_UNIX_EPOCH_ORDINAL = _dt.date(1970, 1, 1).toordinal()
_SECONDS_PER_DAY = 86_400

error = ValueError


class IllegalMonthError(ValueError):
    """Raised for a month number outside 1..12."""

    def __init__(self, month: int) -> None:
        super().__init__(month)
        self.month = month

    def __str__(self) -> str:
        return f"bad month number {self.month}; must be 1-12"


class IllegalWeekdayError(ValueError):
    """Raised for a weekday number outside 0..6."""

    def __init__(self, weekday: int) -> None:
        super().__init__(weekday)
        self.weekday = weekday

    def __str__(self) -> str:
        return f"bad weekday number {self.weekday}; must be 0 (Monday) to 6 (Sunday)"


class Month(IntEnum):
    """The twelve Bikram Sambat months."""

    BAISHAKH = 1
    JESTHA = 2
    ASAR = 3
    SHRAWAN = 4
    BHADRA = 5
    ASHWIN = 6
    KARTIK = 7
    MANGSIR = 8
    POUSH = 9
    MAGH = 10
    FALGUN = 11
    CHAITRA = 12


class Day(IntEnum):
    """Days of the week, numbered as :meth:`date.weekday` (Monday == 0)."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


BAISHAKH, JESTHA, ASAR, SHRAWAN, BHADRA, ASHWIN = (Month(number) for number in range(1, 7))
KARTIK, MANGSIR, POUSH, MAGH, FALGUN, CHAITRA = (Month(number) for number in range(7, 13))
MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = tuple(Day)

month_name: tuple[str, ...] = ("", *EN.month_names)
"""English BS month names; ``month_name[1] == 'Baishakh'`` (index 0 is empty)."""
month_abbr: tuple[str, ...] = ("", *EN.month_abbrs)
"""Abbreviated English BS month names (index 0 is empty)."""
standalone_month_name: tuple[str, ...] = month_name
"""Month names used on their own (Python 3.15+); identical to :data:`month_name` for BS."""
standalone_month_abbr: tuple[str, ...] = month_abbr
"""Abbreviated standalone month names (Python 3.15+); identical to :data:`month_abbr`."""
day_name: tuple[str, ...] = EN.weekday_names
"""English weekday names, Monday first."""
day_abbr: tuple[str, ...] = EN.weekday_abbrs
"""Abbreviated English weekday names, Monday first."""


def _check_month(month: int) -> None:
    if not 1 <= month <= _MONTHS:
        raise IllegalMonthError(month)


def supported_range() -> tuple[int, int]:
    """Return ``(MINYEAR, MAXYEAR)``, the BS years this version supports."""
    return _lookup.MINYEAR, _lookup.MAXYEAR


def days_in_month(year: int, month: int) -> int:
    """Return the number of days (29..32) in a BS month."""
    _check_month(month)
    return _lookup.days_in_month(year, month)


def days_in_year(year: int) -> int:
    """Return the number of days (365 or 366) in a BS year."""
    return _lookup.days_in_year(year)


def isleap(year: int) -> bool:
    """Return whether the BS year has 366 days.

    BS has no leap rule; a year simply has 365 or 366 days.
    """
    return _lookup.days_in_year(year) == 366


def leapdays(y1: int, y2: int) -> int:
    """Return the number of 366-day BS years in ``range(y1, y2)``."""
    return sum(1 for year in range(y1, y2) if isleap(year))


def weekday(year: int, month: int, day: int) -> int:
    """Return the weekday (Monday == 0) of a BS date."""
    return date(year, month, day).weekday()


def monthrange(year: int, month: int) -> tuple[int, int]:
    """Return ``(weekday of the first day, number of days)`` for a BS month.

    Raises:
        IllegalMonthError: If ``month`` is not in 1..12.
    """
    _check_month(month)
    return weekday(year, month, 1), _lookup.days_in_month(year, month)


def _previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, _MONTHS) if month == 1 else (year, month - 1)


def _next_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == _MONTHS else (year, month + 1)


class Calendar:
    """Base class producing BS month and year layouts.

    Args:
        firstweekday: The weekday that starts each week (0 = Monday .. 6 = Sunday).
    """

    def __init__(self, firstweekday: int = 0) -> None:
        self.firstweekday = firstweekday

    @property
    def firstweekday(self) -> int:
        """The first day of the week (0 = Monday .. 6 = Sunday)."""
        return self._firstweekday % _DAYS_PER_WEEK

    @firstweekday.setter
    def firstweekday(self, value: int) -> None:
        self._firstweekday = value

    def getfirstweekday(self) -> int:
        """Return the first weekday."""
        return self.firstweekday

    def setfirstweekday(self, firstweekday: int) -> None:
        """Set the first weekday."""
        self.firstweekday = firstweekday

    def iterweekdays(self) -> Iterator[int]:
        """Yield the seven weekday numbers in display order."""
        for offset in range(self.firstweekday, self.firstweekday + _DAYS_PER_WEEK):
            yield offset % _DAYS_PER_WEEK

    def itermonthdays(self, year: int, month: int) -> Iterator[int]:
        """Yield day numbers for a month layout, with 0 for padding days."""
        day1, ndays = monthrange(year, month)
        before = (day1 - self.firstweekday) % _DAYS_PER_WEEK
        yield from repeat(0, before)
        yield from range(1, ndays + 1)
        after = (self.firstweekday - day1 - ndays) % _DAYS_PER_WEEK
        yield from repeat(0, after)

    def itermonthdays2(self, year: int, month: int) -> Iterator[tuple[int, int]]:
        """Yield ``(day, weekday)`` pairs, with day 0 for padding days."""
        for position, day in enumerate(self.itermonthdays(year, month), self.firstweekday):
            yield day, position % _DAYS_PER_WEEK

    def itermonthdays3(self, year: int, month: int) -> Iterator[tuple[int, int, int]]:
        """Yield ``(year, month, day)`` triples covering complete weeks."""
        day1, ndays = monthrange(year, month)
        before = (day1 - self.firstweekday) % _DAYS_PER_WEEK
        after = (self.firstweekday - day1 - ndays) % _DAYS_PER_WEEK
        if before:
            prev_year, prev_month = _previous_month(year, month)
            end = _lookup.days_in_month(prev_year, prev_month) + 1
            for day in range(end - before, end):
                yield prev_year, prev_month, day
        for day in range(1, ndays + 1):
            yield year, month, day
        if after:
            next_year, next_month = _next_month(year, month)
            for day in range(1, after + 1):
                yield next_year, next_month, day

    def itermonthdays4(self, year: int, month: int) -> Iterator[tuple[int, int, int, int]]:
        """Yield ``(year, month, day, weekday)`` tuples covering complete weeks."""
        for position, (y, m, d) in enumerate(self.itermonthdays3(year, month)):
            yield y, m, d, (self.firstweekday + position) % _DAYS_PER_WEEK

    def itermonthdates(self, year: int, month: int) -> Iterator[date]:
        """Yield :class:`sambat.date` objects covering complete weeks."""
        for y, m, d in self.itermonthdays3(year, month):
            yield date(y, m, d)

    def monthdatescalendar(self, year: int, month: int) -> list[list[date]]:
        """Return the month as a list of weeks of :class:`sambat.date`."""
        return _chunk(list(self.itermonthdates(year, month)), _DAYS_PER_WEEK)

    def monthdays2calendar(self, year: int, month: int) -> list[list[tuple[int, int]]]:
        """Return the month as a list of weeks of ``(day, weekday)`` pairs."""
        return _chunk(list(self.itermonthdays2(year, month)), _DAYS_PER_WEEK)

    def monthdayscalendar(self, year: int, month: int) -> list[list[int]]:
        """Return the month as a list of weeks of day numbers (0 for padding)."""
        return _chunk(list(self.itermonthdays(year, month)), _DAYS_PER_WEEK)

    def yeardatescalendar(self, year: int, width: int = 3) -> list[list[list[list[date]]]]:
        """Return the year as rows of ``width`` months of weeks of dates."""
        months = [self.monthdatescalendar(year, number) for number in range(1, _MONTHS + 1)]
        return _chunk(months, width)

    def yeardays2calendar(
        self, year: int, width: int = 3
    ) -> list[list[list[list[tuple[int, int]]]]]:
        """Return the year as rows of ``width`` months of ``(day, weekday)`` weeks."""
        months = [self.monthdays2calendar(year, number) for number in range(1, _MONTHS + 1)]
        return _chunk(months, width)

    def yeardayscalendar(self, year: int, width: int = 3) -> list[list[list[list[int]]]]:
        """Return the year as rows of ``width`` months of day-number weeks."""
        months = [self.monthdayscalendar(year, number) for number in range(1, _MONTHS + 1)]
        return _chunk(months, width)


def _chunk(items: list[_T], size: int) -> list[list[_T]]:
    return [items[start : start + size] for start in range(0, len(items), size)]


def _truncate(text: str, width: int) -> str:
    """Return the first ``width`` characters, keeping combining marks attached.

    Devanagari vowel signs and viramas (Unicode categories Mn and Mc) belong to
    the preceding letter, so cutting between them would produce broken text.
    """
    taken = 0
    for position, char in enumerate(text):
        if unicodedata.category(char) in {"Mn", "Mc"}:
            continue
        if taken == width:
            return text[:position]
        taken += 1
    return text


class TextCalendar(Calendar):
    """Plain-text BS calendars with English names (see :class:`LocaleTextCalendar`)."""

    locale: Locale = EN

    def prweek(self, theweek: Sequence[tuple[int, int]], width: int) -> None:
        """Print one week (no trailing newline)."""
        print(self.formatweek(theweek, width), end="")

    def formatday(self, day: int, weekday: int, width: int) -> str:
        """Return a day number centred in ``width`` columns (blank for 0)."""
        text = "" if day == 0 else self.locale.format_number(f"{day:2d}")
        return text.center(width)

    def formatweek(self, theweek: Sequence[tuple[int, int]], width: int) -> str:
        """Return one week as a single line."""
        return " ".join(self.formatday(day, wd, width) for day, wd in theweek)

    def formatweekday(self, day: int, width: int) -> str:
        """Return a weekday name truncated and centred to ``width`` columns."""
        names = self.locale.weekday_names if width >= 9 else self.locale.weekday_abbrs
        return _truncate(names[day], width).center(width)

    def formatweekheader(self, width: int) -> str:
        """Return the weekday header line."""
        return " ".join(self.formatweekday(day, width) for day in self.iterweekdays())

    def formatmonthname(
        self,
        theyear: int,
        themonth: int,
        width: int,
        withyear: bool = True,  # noqa: FBT001, FBT002
    ) -> str:
        """Return the month name (and year) centred in ``width`` columns."""
        _check_month(themonth)
        text = self.locale.month_names[themonth - 1]
        if withyear:
            text = f"{text} {self.locale.format_number(str(theyear))}"
        return text.center(width)

    def prmonth(self, theyear: int, themonth: int, w: int = 0, l: int = 0) -> None:  # noqa: E741
        """Print a month calendar."""
        print(self.formatmonth(theyear, themonth, w, l), end="")

    def formatmonth(self, theyear: int, themonth: int, w: int = 0, l: int = 0) -> str:  # noqa: E741
        """Return a month calendar as a multi-line string."""
        w = max(2, w)
        l = max(1, l)  # noqa: E741
        text = self.formatmonthname(theyear, themonth, 7 * (w + 1) - 1).rstrip()
        text += "\n" * l
        text += self.formatweekheader(w).rstrip()
        text += "\n" * l
        for week in self.monthdays2calendar(theyear, themonth):
            text += self.formatweek(week, w).rstrip()
            text += "\n" * l
        return text

    def formatyear(self, theyear: int, w: int = 2, l: int = 1, c: int = 6, m: int = 3) -> str:  # noqa: E741
        """Return a whole year as a multi-line string, ``m`` months per row."""
        w = max(2, w)
        l = max(1, l)  # noqa: E741
        c = max(2, c)
        colwidth = (w + 1) * 7 - 1
        parts = [
            self.locale.format_number(str(theyear)).center(colwidth * m + c * (m - 1)).rstrip()
        ]
        parts.append("\n" * l)
        header = self.formatweekheader(w)
        for row_index, row in enumerate(self.yeardays2calendar(theyear, m)):
            months = range(m * row_index + 1, min(m * (row_index + 1) + 1, _MONTHS + 1))
            parts.append("\n" * l)
            names = (self.formatmonthname(theyear, k, colwidth, withyear=False) for k in months)
            parts.append(formatstring(names, colwidth, c).rstrip())
            parts.append("\n" * l)
            parts.append(formatstring((header for _ in months), colwidth, c).rstrip())
            parts.append("\n" * l)
            height = max(len(month_weeks) for month_weeks in row)
            for line in range(height):
                weeks = [
                    self.formatweek(month_weeks[line], w) if line < len(month_weeks) else ""
                    for month_weeks in row
                ]
                parts.append(formatstring(weeks, colwidth, c).rstrip())
                parts.append("\n" * l)
        return "".join(parts)

    def pryear(self, theyear: int, w: int = 0, l: int = 0, c: int = 6, m: int = 3) -> None:  # noqa: E741
        """Print a whole year."""
        print(self.formatyear(theyear, w, l, c, m), end="")


class HTMLCalendar(Calendar):
    """HTML BS calendars with English names (see :class:`LocaleHTMLCalendar`)."""

    locale: Locale = EN
    cssclasses: Sequence[str] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
    cssclasses_weekday_head: Sequence[str] = cssclasses
    cssclass_noday = "noday"
    cssclass_month_head = "month"
    cssclass_month = "month"
    cssclass_year_head = "year"
    cssclass_year = "year"

    def formatday(self, day: int, weekday: int) -> str:
        """Return one table cell."""
        if day == 0:
            return f'<td class="{self.cssclass_noday}">&nbsp;</td>'
        return f'<td class="{self.cssclasses[weekday]}">{self.locale.format_number(str(day))}</td>'

    def formatweek(self, theweek: Sequence[tuple[int, int]]) -> str:
        """Return one table row."""
        cells = "".join(self.formatday(day, wd) for day, wd in theweek)
        return f"<tr>{cells}</tr>"

    def formatweekday(self, day: int) -> str:
        """Return one header cell."""
        name = html.escape(self.locale.weekday_abbrs[day])
        return f'<th class="{self.cssclasses_weekday_head[day]}">{name}</th>'

    def formatweekheader(self) -> str:
        """Return the header row."""
        cells = "".join(self.formatweekday(day) for day in self.iterweekdays())
        return f"<tr>{cells}</tr>"

    def formatmonthname(
        self,
        theyear: int,
        themonth: int,
        withyear: bool = True,  # noqa: FBT001, FBT002
    ) -> str:
        """Return the month-name header row."""
        _check_month(themonth)
        text = self.locale.month_names[themonth - 1]
        if withyear:
            text = f"{text} {self.locale.format_number(str(theyear))}"
        return (
            f'<tr><th colspan="7" class="{self.cssclass_month_head}">{html.escape(text)}</th></tr>'
        )

    def formatmonth(
        self,
        theyear: int,
        themonth: int,
        withyear: bool = True,  # noqa: FBT001, FBT002
    ) -> str:
        """Return a month as an HTML table."""
        rows = [
            f'<table border="0" cellpadding="0" cellspacing="0" class="{self.cssclass_month}">',
            self.formatmonthname(theyear, themonth, withyear=withyear),
            self.formatweekheader(),
        ]
        rows += [self.formatweek(week) for week in self.monthdays2calendar(theyear, themonth)]
        rows.append("</table>")
        return "\n".join(rows) + "\n"

    def formatyear(self, theyear: int, width: int = 3) -> str:
        """Return a year as an HTML table with ``width`` months per row."""
        width = max(width, 1)
        year_label = self.locale.format_number(str(theyear))
        parts = [
            f'<table border="0" cellpadding="0" cellspacing="0" class="{self.cssclass_year}">',
            "\n",
            f'<tr><th colspan="{width}" class="{self.cssclass_year_head}">{year_label}</th></tr>',
        ]
        for start in range(1, _MONTHS + 1, width):
            parts.append("<tr>")
            parts.extend(
                f"<td>{self.formatmonth(theyear, number, withyear=False)}</td>"
                for number in range(start, min(start + width, _MONTHS + 1))
            )
            parts.append("</tr>")
        parts.append("</table>")
        return "".join(parts)

    def formatyearpage(
        self,
        theyear: int,
        width: int = 3,
        css: str | None = "calendar.css",
        encoding: str | None = None,
    ) -> bytes:
        """Return a complete HTML page for a year, encoded as bytes."""
        return self._format_html_page(theyear, self.formatyear(theyear, width), css, encoding)

    def formatmonthpage(
        self,
        theyear: int,
        themonth: int,
        *,
        css: str | None = "calendar.css",
        encoding: str | None = None,
    ) -> bytes:
        """Return a complete HTML page for one month, encoded as bytes."""
        return self._format_html_page(theyear, self.formatmonth(theyear, themonth), css, encoding)

    def _format_html_page(
        self, theyear: int, content: str, css: str | None, encoding: str | None
    ) -> bytes:
        encoding = encoding or "utf-8"
        lang = html.escape(self.locale.name)
        title = f"Calendar for BS {self.locale.format_number(str(theyear))}"
        lines = [
            "<!DOCTYPE html>",
            f'<html lang="{lang}">',
            "<head>",
            f'<meta charset="{html.escape(encoding)}">',
        ]
        if css is not None:
            lines.append(f'<link rel="stylesheet" href="{html.escape(css)}">')
        lines += [f"<title>{html.escape(title)}</title>", "</head>", "<body>", content]
        lines += ["</body>", "</html>", ""]
        return "\n".join(lines).encode(encoding, "xmlcharrefreplace")


class LocaleTextCalendar(TextCalendar):
    """A :class:`TextCalendar` using a sambat :class:`~sambat.locale.Locale`.

    Args:
        firstweekday: The first weekday (0 = Monday .. 6 = Sunday).
        locale: The locale to use (default English).
    """

    locale: Locale

    def __init__(self, firstweekday: int = 0, locale: Locale | None = None) -> None:
        super().__init__(firstweekday)
        self.locale = locale or EN


class LocaleHTMLCalendar(HTMLCalendar):
    """An :class:`HTMLCalendar` using a sambat :class:`~sambat.locale.Locale`.

    Args:
        firstweekday: The first weekday (0 = Monday .. 6 = Sunday).
        locale: The locale to use (default English).
    """

    locale: Locale

    def __init__(self, firstweekday: int = 0, locale: Locale | None = None) -> None:
        super().__init__(firstweekday)
        self.locale = locale or EN


def _month_cells(cal: Calendar, year: int, month: int) -> list[list[tuple[int, int, int]]]:
    """Return weeks of ``(bs_day, weekday, ad_day)``; day 0 marks padding."""
    first = date(year, month, 1).toordinal()
    weeks: list[list[tuple[int, int, int]]] = []
    for week in cal.monthdays2calendar(year, month):
        cells: list[tuple[int, int, int]] = []
        for day, wd in week:
            ad_day = _dt.date.fromordinal(first + day - 1).day if day else 0
            cells.append((day, wd, ad_day))
        weeks.append(cells)
    return weeks


def _gregorian_span(year: int, month: int) -> str:
    start = date(year, month, 1).to_gregorian()
    end = date(year, month, _lookup.days_in_month(year, month)).to_gregorian()
    if start.year == end.year:
        return f"{start:%b}–{end:%b} {end.year}"
    return f"{start:%b} {start.year}–{end:%b} {end.year}"


class DualTextCalendar(LocaleTextCalendar):
    """Text calendar showing each BS day with its Gregorian day number.

    Weeks start on Sunday by default, as on printed Nepali calendars.

    Args:
        firstweekday: The first weekday (default 6 = Sunday).
        locale: The locale for BS names and digits (default English).
    """

    def __init__(self, firstweekday: int = 6, locale: Locale | None = None) -> None:
        super().__init__(firstweekday, locale)

    def formatmonth(self, theyear: int, themonth: int, w: int = 0, l: int = 0) -> str:  # noqa: E741
        """Return a month where each cell reads ``"<BS day> <AD day>"``."""
        width = max(5, w)
        l = max(1, l)  # noqa: E741
        title = self.formatmonthname(theyear, themonth, 0).strip()
        title = f"{title} ({_gregorian_span(theyear, themonth)})"
        lines = [title.center(7 * (width + 1) - 1).rstrip(), self.formatweekheader(width).rstrip()]
        for week in _month_cells(self, theyear, themonth):
            cells: list[str] = []
            for day, _, ad_day in week:
                if day == 0:
                    cells.append(" " * width)
                else:
                    bs = self.locale.format_number(f"{day:2d}")
                    cells.append(f"{bs} {ad_day:2d}".rjust(width))
            lines.append(" ".join(cells).rstrip())
        return ("\n" * l).join(lines) + "\n" * l


class DualHTMLCalendar(LocaleHTMLCalendar):
    """HTML calendar showing each BS day with its Gregorian day number.

    Each day cell contains the BS day followed by
    ``<span class="ad">AD day</span>``. Weeks start on Sunday by default.

    Args:
        firstweekday: The first weekday (default 6 = Sunday).
        locale: The locale for BS names and digits (default English).
    """

    cssclass_ad = "ad"

    def __init__(self, firstweekday: int = 6, locale: Locale | None = None) -> None:
        super().__init__(firstweekday, locale)

    def formatmonth(
        self,
        theyear: int,
        themonth: int,
        withyear: bool = True,  # noqa: FBT001, FBT002
    ) -> str:
        """Return a month table whose cells include the Gregorian day."""
        rows = [
            f'<table border="0" cellpadding="0" cellspacing="0" class="{self.cssclass_month}">',
            self.formatmonthname(theyear, themonth, withyear=withyear),
            self.formatweekheader(),
        ]
        for week in _month_cells(self, theyear, themonth):
            cells: list[str] = []
            for day, wd, ad_day in week:
                if day == 0:
                    cells.append(f'<td class="{self.cssclass_noday}">&nbsp;</td>')
                else:
                    bs = self.locale.format_number(str(day))
                    cells.append(
                        f'<td class="{self.cssclasses[wd]}">{bs}'
                        f'<span class="{self.cssclass_ad}">{ad_day}</span></td>'
                    )
            rows.append(f"<tr>{''.join(cells)}</tr>")
        rows.append("</table>")
        return "\n".join(rows) + "\n"


# ------------------------------------------------------------ module-level API

_SPACING = 6
_COLWIDTH = 7 * 3 - 1

c: TextCalendar = TextCalendar()

firstweekday: Callable[[], int] = c.getfirstweekday
monthcalendar: Callable[[int, int], list[list[int]]] = c.monthdayscalendar
prweek: Callable[[Sequence[tuple[int, int]], int], None] = c.prweek
week: Callable[[Sequence[tuple[int, int]], int], str] = c.formatweek
weekheader: Callable[[int], str] = c.formatweekheader
prmonth: Callable[..., None] = c.prmonth
month: Callable[..., str] = c.formatmonth
calendar: Callable[..., str] = c.formatyear
prcal: Callable[..., None] = c.pryear


def setfirstweekday(firstweekday: int) -> None:
    """Set the first weekday used by the module-level functions.

    Raises:
        IllegalWeekdayError: If ``firstweekday`` is not in 0..6.
    """
    if not MONDAY <= firstweekday <= SUNDAY:
        raise IllegalWeekdayError(firstweekday)
    c.firstweekday = firstweekday


def formatstring(cols: Iterable[str], colwidth: int = _COLWIDTH, spacing: int = _SPACING) -> str:
    """Return ``cols`` centred in ``colwidth`` columns and joined by ``spacing`` spaces."""
    return (" " * spacing).join(column.center(colwidth) for column in cols)


def format(cols: Iterable[str], colwidth: int = _COLWIDTH, spacing: int = _SPACING) -> None:  # noqa: A001
    """Print ``formatstring(cols, colwidth, spacing)``."""
    print(formatstring(cols, colwidth, spacing))


def timegm(tuple: Sequence[int]) -> int:  # noqa: A002
    """Return the POSIX timestamp of a UTC BS ``(year, month, day, hour, minute, second)`` tuple.

    The inverse of ``sambat.datetime.utctimetuple()`` followed by this function.
    """
    year, month, day, hour, minute, second = tuple[:6]
    days = _lookup.ymd_to_ordinal(year, month, day) - _UNIX_EPOCH_ORDINAL
    return ((days * 24 + hour) * 60 + minute) * 60 + second


def _locale_argument(name: str) -> Locale:
    try:
        return get_locale(name)
    except LookupError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def main(args: Sequence[str] | None = None) -> int:
    """Run the ``python -m sambat.calendar`` command line interface.

    Args:
        args: Command line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        The process exit status.
    """
    parser = argparse.ArgumentParser(
        prog="python -m sambat.calendar", description="Print a Bikram Sambat calendar."
    )
    parser.add_argument("year", nargs="?", type=int, help="BS year (default: this year)")
    parser.add_argument("month", nargs="?", type=int, help="BS month number, 1-12")
    parser.add_argument("-t", "--type", choices=("text", "html"), default="text")
    parser.add_argument(
        "-L", "--locale", type=_locale_argument, default=EN, help="en or ne (default: en)"
    )
    parser.add_argument(
        "-f", "--first-weekday", type=int, default=None, help="0=Monday .. 6=Sunday"
    )
    parser.add_argument("--dual", action="store_true", help="show Gregorian day numbers")
    parser.add_argument("-w", "--width", type=int, default=2, help="text day column width")
    parser.add_argument("-l", "--lines", type=int, default=1, help="text lines per week")
    parser.add_argument("-s", "--spacing", type=int, default=6, help="text spacing between months")
    parser.add_argument("-m", "--months", type=int, default=3, help="months per row")
    options = parser.parse_args(args)

    locale: Locale = options.locale
    default_first = SUNDAY if options.dual else MONDAY
    first = default_first if options.first_weekday is None else options.first_weekday
    if not MONDAY <= first <= SUNDAY:
        parser.error(str(IllegalWeekdayError(first)))
    year = options.year if options.year is not None else date.today().year
    if options.month is not None and not 1 <= options.month <= _MONTHS:
        parser.error(str(IllegalMonthError(options.month)))

    try:
        output = _render(options, locale, first, year)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(output)
    return 0


def _render(options: argparse.Namespace, locale: Locale, first: int, year: int) -> str:
    if options.type == "html":
        html_cal = (
            DualHTMLCalendar(first, locale) if options.dual else LocaleHTMLCalendar(first, locale)
        )
        if options.month is not None:
            return html_cal.formatmonth(year, options.month)
        return html_cal.formatyearpage(year, options.months).decode("utf-8")
    text_cal = (
        DualTextCalendar(first, locale) if options.dual else LocaleTextCalendar(first, locale)
    )
    if options.month is not None:
        return text_cal.formatmonth(year, options.month, options.width, options.lines)
    if options.dual:
        return "\n".join(text_cal.formatmonth(year, number) for number in range(1, _MONTHS + 1))
    return text_cal.formatyear(year, options.width, options.lines, options.spacing, options.months)


if __name__ == "__main__":
    raise SystemExit(main())
