"""Nepal's fiscal year and its standard subdivisions.

The Government of Nepal's fiscal year starts on Shrawan 1 and ends on the
last day of Asar of the next BS year, so fiscal year ``2083/84`` runs from
2083-04-01 to the end of Asar 2084. It is divided into:

* four quarters (त्रैमासिक) of three months: Shrawan-Asoj, Kartik-Poush,
  Magh-Chaitra and Baishakh-Asar;
* three chaumasik (चौमासिक) periods of four months, used for budget reviews:
  Shrawan-Kartik, Mangsir-Falgun and Chaitra-Asar;
* two halves (अर्धवार्षिक) of six months: Shrawan-Poush and Magh-Asar.

Organisations whose year starts in another month can pass ``start_month``.

A fiscal year that ends after :data:`sambat.MAXYEAR` can still be created and
queried; only boundaries that fall in unpublished BS years raise ``ValueError``.

Examples:
    >>> from sambat import date
    >>> from sambat.fiscal import FiscalYear
    >>> fy = FiscalYear.of(date(2083, 6, 15))
    >>> fy.label
    '2083/84'
    >>> fy.quarter_of(date(2083, 6, 15)), fy.chaumasik_of(date(2083, 6, 15))
    (1, 1)
    >>> fy.quarter(1)
    Period(sambat.date(2083, 4, 1), sambat.date(2083, 6, 31))
"""

from __future__ import annotations

import datetime as _dt
import re
from typing import TYPE_CHECKING, Self

from sambat._date import date
from sambat.periods import MonthPeriod, Period
from sambat.text import to_ascii_digits, to_nepali_digits

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["SHRAWAN", "FiscalYear"]

SHRAWAN = 4
"""The month (Shrawan) in which Nepal's government fiscal year starts."""

_MONTHS = 12
_LABEL = re.compile(r"^\s*(\d{4})\s*[/\-]\s*(\d{2}|\d{4})\s*$")


class FiscalYear:
    """A fiscal year identified by the BS year in which it starts.

    Args:
        start_year: The BS year containing the first day (2083 for ``2083/84``).
        start_month: The first month (default 4, Shrawan).

    Raises:
        ValueError: If ``start_month`` is not in 1..12.
    """

    __slots__ = ("start_month", "start_year")

    start_year: int
    start_month: int

    def __init__(self, start_year: int, *, start_month: int = SHRAWAN) -> None:
        if not 1 <= start_month <= _MONTHS:
            message = f"start_month must be in 1..12, not {start_month}"
            raise ValueError(message)
        self.start_year = start_year
        self.start_month = start_month

    # ---------------------------------------------------------- constructors

    @classmethod
    def of(cls, value: date, *, start_month: int = SHRAWAN) -> Self:
        """Return the fiscal year that contains ``value``.

        Args:
            value: A sambat ``date`` or ``datetime``.
            start_month: The first month of the fiscal year.

        Returns:
            The containing fiscal year.
        """
        year = value.year if value.month >= start_month else value.year - 1
        return cls(year, start_month=start_month)

    @classmethod
    def from_label(cls, label: str, *, start_month: int = SHRAWAN) -> Self:
        """Parse a label such as ``"2083/84"``, ``"2083-2084"`` or ``"२०८३/८४"``.

        Args:
            label: The fiscal year label.
            start_month: The first month of the fiscal year.

        Returns:
            The fiscal year.

        Raises:
            ValueError: If the label is malformed or its two years do not follow
                each other.
        """
        found = _LABEL.match(to_ascii_digits(label))
        if found is None:
            message = f"invalid fiscal year label {label!r}; expected e.g. '2083/84'"
            raise ValueError(message)
        first, second = int(found.group(1)), found.group(2)
        expected = f"{first + 1:04d}" if len(second) == 4 else f"{(first + 1) % 100:02d}"
        if second != expected:
            message = f"invalid fiscal year label {label!r}; the second year must follow the first"
            raise ValueError(message)
        return cls(first, start_month=start_month)

    # ------------------------------------------------------------ properties

    @property
    def label(self) -> str:
        """The conventional label, e.g. ``"2083/84"``."""
        if self.start_month == 1:
            return f"{self.start_year}"
        return f"{self.start_year}/{(self.start_year + 1) % 100:02d}"

    @property
    def label_ne(self) -> str:
        """The label in Devanagari digits, e.g. ``"२०८३/८४"``."""
        return to_nepali_digits(self.label)

    @property
    def start(self) -> date:
        """The first day of the fiscal year."""
        return date(self.start_year, self.start_month, 1)

    @property
    def end(self) -> date:
        """The last day of the fiscal year.

        Raises:
            ValueError: If that day falls in a BS year not yet in the calendar table.
        """
        return self._month(_MONTHS - 1).end

    @property
    def days(self) -> int:
        """The number of days in the fiscal year."""
        span: _dt.timedelta = self.end - self.start
        return span.days + 1

    def _month(self, index: int) -> MonthPeriod:
        """Return month ``index`` (0-based) of the fiscal year."""
        offset = self.start_month - 1 + index
        return MonthPeriod(self.start_year + offset // _MONTHS, offset % _MONTHS + 1)

    def months(self) -> list[MonthPeriod]:
        """Return the twelve months of the fiscal year, in order."""
        return [self._month(index) for index in range(_MONTHS)]

    def iter_months(self) -> Iterator[MonthPeriod]:
        """Yield the months of the fiscal year lazily.

        Unlike :meth:`months`, this works for fiscal years that extend past
        :data:`sambat.MAXYEAR` until the first unpublished month is reached.
        """
        for index in range(_MONTHS):
            yield self._month(index)

    # ---------------------------------------------------------- subdivisions

    def _span(self, number: int, size: int) -> Period:
        count = _MONTHS // size
        if not 1 <= number <= count:
            message = f"number must be in 1..{count}, not {number}"
            raise ValueError(message)
        first = self._month((number - 1) * size)
        last = self._month(number * size - 1)
        return Period(first.start, last.end)

    def quarter(self, number: int) -> Period:
        """Return quarter ``number`` (1..4), three months each."""
        return self._span(number, 3)

    def chaumasik(self, number: int) -> Period:
        """Return chaumasik period ``number`` (1..3), four months each."""
        return self._span(number, 4)

    def half(self, number: int) -> Period:
        """Return half ``number`` (1..2), six months each."""
        return self._span(number, 6)

    def fiscal_month(self, value: date) -> int:
        """Return the 1-based month of the fiscal year in which ``value`` falls.

        Raises:
            ValueError: If ``value`` is not in this fiscal year.
        """
        self._require(value)
        return (value.month - self.start_month) % _MONTHS + 1

    def quarter_of(self, value: date) -> int:
        """Return the quarter (1..4) containing ``value``."""
        return (self.fiscal_month(value) - 1) // 3 + 1

    def chaumasik_of(self, value: date) -> int:
        """Return the chaumasik period (1..3) containing ``value``."""
        return (self.fiscal_month(value) - 1) // 4 + 1

    def half_of(self, value: date) -> int:
        """Return the half (1..2) containing ``value``."""
        return (self.fiscal_month(value) - 1) // 6 + 1

    # ------------------------------------------------------------- protocol

    def _require(self, value: date) -> None:
        if value not in self:
            message = f"{value!s} is not in fiscal year {self.label}"
            raise ValueError(message)

    def __contains__(self, value: object) -> bool:
        if not isinstance(value, date):
            return False
        return FiscalYear.of(value, start_month=self.start_month) == self

    def next(self) -> FiscalYear:
        """Return the following fiscal year."""
        return FiscalYear(self.start_year + 1, start_month=self.start_month)

    def prev(self) -> FiscalYear:
        """Return the preceding fiscal year."""
        return FiscalYear(self.start_year - 1, start_month=self.start_month)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FiscalYear):
            return NotImplemented
        return (self.start_year, self.start_month) == (other.start_year, other.start_month)

    def __hash__(self) -> int:
        return hash((self.start_year, self.start_month))

    def __lt__(self, other: FiscalYear) -> bool:
        if not isinstance(other, FiscalYear) or other.start_month != self.start_month:
            return NotImplemented
        return self.start_year < other.start_year

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        if self.start_month == SHRAWAN:
            return f"FiscalYear({self.start_year})"
        return f"FiscalYear({self.start_year}, start_month={self.start_month})"
