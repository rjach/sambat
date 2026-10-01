"""Names, digits and format templates used by ``strftime`` and ``strptime``.

A :class:`Locale` is an immutable bundle of the strings that differ between
languages. Two locales are built in:

* :data:`EN` - English transliterations with ASCII digits (the default).
* :data:`NE` - Nepali in Devanagari script with Devanagari digits.

Locales are always passed explicitly (``d.strftime(fmt, locale=NE)``); the
process-wide C locale is never consulted, so output is identical on every
platform and thread-safe.

Examples:
    >>> import dataclasses
    >>> from sambat import date
    >>> from sambat.locale import NE
    >>> date(2083, 6, 15).strftime("%d %B %Y", locale=NE)
    '१५ असोज २०८३'
    >>> ne_ascii = dataclasses.replace(NE, digits="0123456789")
    >>> date(2083, 6, 15).strftime("%d %B %Y", locale=ne_ascii)
    '15 असोज 2083'
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sambat.text import ASCII_DIGITS, DEVANAGARI_DIGITS

__all__ = ["ASCII_DIGITS", "DEVANAGARI_DIGITS", "EN", "NE", "Locale", "get_locale"]

_MONTHS = 12
_WEEKDAYS = 7
_DIGITS = 10


@dataclass(frozen=True, slots=True)
class Locale:
    """Language-specific strings for formatting and parsing BS dates.

    Weekday sequences start on Monday, matching ``date.weekday()``.

    Attributes:
        name: A short identifier such as ``"en"`` or ``"ne"``.
        month_names: The 12 BS month names, Baishakh first (``%B``).
        month_abbrs: The 12 abbreviated month names (``%b``).
        weekday_names: The 7 weekday names, Monday first (``%A``).
        weekday_abbrs: The 7 abbreviated weekday names (``%a``).
        am_pm: The ante/post meridiem markers (``%p``).
        digits: The ten digits used for numeric fields, in value order.
        datetime_format: The expansion of ``%c``.
        date_format: The expansion of ``%x``.
        time_format: The expansion of ``%X``.
        month_aliases: Extra spellings accepted when parsing each month.
        weekday_aliases: Extra spellings accepted when parsing each weekday.
    """

    name: str
    month_names: tuple[str, ...]
    month_abbrs: tuple[str, ...]
    weekday_names: tuple[str, ...]
    weekday_abbrs: tuple[str, ...]
    am_pm: tuple[str, str]
    digits: str
    datetime_format: str
    date_format: str
    time_format: str
    month_aliases: tuple[tuple[str, ...], ...] = field(default=((),) * _MONTHS)
    weekday_aliases: tuple[tuple[str, ...], ...] = field(default=((),) * _WEEKDAYS)

    def __post_init__(self) -> None:
        """Validate the sequence lengths.

        Raises:
            ValueError: If a sequence has the wrong number of entries.
        """
        expected = {
            "month_names": (self.month_names, _MONTHS),
            "month_abbrs": (self.month_abbrs, _MONTHS),
            "month_aliases": (self.month_aliases, _MONTHS),
            "weekday_names": (self.weekday_names, _WEEKDAYS),
            "weekday_abbrs": (self.weekday_abbrs, _WEEKDAYS),
            "weekday_aliases": (self.weekday_aliases, _WEEKDAYS),
            "am_pm": (self.am_pm, 2),
        }
        for attribute, (values, size) in expected.items():
            if len(values) != size:
                message = f"Locale.{attribute} needs {size} entries, got {len(values)}"
                raise ValueError(message)
        if len(self.digits) != _DIGITS or len(set(self.digits)) != _DIGITS:
            message = "Locale.digits must contain 10 distinct characters"
            raise ValueError(message)

    def format_number(self, text: str) -> str:
        """Render the ASCII digits in ``text`` with this locale's digits.

        Args:
            text: A string that may contain ASCII digits.

        Returns:
            The string with digits mapped to :attr:`digits`.
        """
        if self.digits == ASCII_DIGITS:
            return text
        return text.translate(str.maketrans(ASCII_DIGITS, self.digits))

    def month_spellings(self, month: int) -> tuple[str, ...]:
        """Return every spelling accepted when parsing ``month`` (1..12).

        Args:
            month: A month number in 1..12.

        Returns:
            The full name, abbreviation and aliases, without duplicates.
        """
        index = month - 1
        spellings = (self.month_names[index], self.month_abbrs[index], *self.month_aliases[index])
        return tuple(dict.fromkeys(spellings))

    def weekday_spellings(self, weekday: int) -> tuple[str, ...]:
        """Return every spelling accepted when parsing ``weekday`` (Monday = 0).

        Args:
            weekday: A weekday number in 0..6.

        Returns:
            The full name, abbreviation and aliases, without duplicates.
        """
        spellings = (
            self.weekday_names[weekday],
            self.weekday_abbrs[weekday],
            *self.weekday_aliases[weekday],
        )
        return tuple(dict.fromkeys(spellings))


EN = Locale(
    name="en",
    month_names=(
        "Baishakh",
        "Jestha",
        "Asar",
        "Shrawan",
        "Bhadra",
        "Ashwin",
        "Kartik",
        "Mangsir",
        "Poush",
        "Magh",
        "Falgun",
        "Chaitra",
    ),
    month_abbrs=(
        "Bai",
        "Jes",
        "Asa",
        "Shr",
        "Bha",
        "Ash",
        "Kar",
        "Man",
        "Pou",
        "Mag",
        "Fal",
        "Cha",
    ),
    weekday_names=("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    weekday_abbrs=("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
    am_pm=("AM", "PM"),
    digits=ASCII_DIGITS,
    datetime_format="%a %b %e %H:%M:%S %Y",
    date_format="%m/%d/%y",
    time_format="%H:%M:%S",
    month_aliases=(
        ("Baisakh", "Baishak", "Baisak", "Vaishakh", "Vaisakh", "Vaishakha"),
        ("Jeth", "Jyeshtha", "Jyestha", "Jestha", "Jaistha", "Jesth"),
        ("Ashadh", "Asadh", "Ashar", "Aashadh", "Ashad", "Asad"),
        ("Saun", "Sawan", "Shravan", "Srawan", "Sravan"),
        ("Bhadau", "Bhado", "Bhadrapad", "Bhadra"),
        ("Asoj", "Ashoj", "Aswin", "Ashvin", "Asvin", "Aswhin"),
        ("Kattik", "Kartika", "Karthik", "Kartick"),
        ("Mansir", "Mangshir", "Marga", "Margashirsha", "Mangshir"),
        ("Push", "Paush", "Pous", "Pausha", "Pus"),
        ("Magha",),
        ("Phagun", "Phalgun", "Fagun", "Phalguna", "Falgun"),
        ("Chait", "Chaitr", "Chaita"),
    ),
    weekday_aliases=(
        ("Sombar", "Sombaar"),
        ("Tues", "Mangalbar", "Mangalbaar"),
        ("Budhbar", "Budhabar", "Budhbaar"),
        ("Thur", "Thurs", "Bihibar", "Bihibaar"),
        ("Sukrabar", "Shukrabar", "Sukrabaar"),
        ("Sanibar", "Shanibar", "Sanibaar"),
        ("Aaitabar", "Aitabar", "Aaitbar", "Aitbar"),
    ),
)
"""English month and weekday names with ASCII digits."""

NE = Locale(
    name="ne",
    month_names=(
        "बैशाख",
        "जेठ",
        "असार",
        "साउन",
        "भदौ",
        "असोज",
        "कात्तिक",
        "मंसिर",
        "पुस",
        "माघ",
        "फागुन",
        "चैत",
    ),
    month_abbrs=(
        "बैशाख",
        "जेठ",
        "असार",
        "साउन",
        "भदौ",
        "असोज",
        "कात्तिक",
        "मंसिर",
        "पुस",
        "माघ",
        "फागुन",
        "चैत",
    ),
    weekday_names=("सोमबार", "मङ्गलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार", "आइतबार"),
    weekday_abbrs=("सोम", "मङ्गल", "बुध", "बिही", "शुक्र", "शनि", "आइत"),
    am_pm=("पूर्वाह्न", "अपराह्न"),
    digits=DEVANAGARI_DIGITS,
    datetime_format="%Y %B %d, %A %H:%M:%S",
    date_format="%Y/%m/%d",
    time_format="%H:%M:%S",
    month_aliases=(
        ("वैशाख", "बैसाख", "वैसाख"),
        ("ज्येष्ठ", "जेष्ठ", "जेठ"),
        ("आषाढ", "असाढ", "अषाढ"),
        ("श्रावण", "सावन"),
        ("भाद्र", "भाद्रपद"),
        ("आश्विन", "असोझ"),
        ("कार्तिक", "कातिक"),
        ("मङ्सिर", "मार्गशीर्ष", "मङ्गसिर", "मंगसिर"),
        ("पौष", "पूस"),
        ("माघ",),
        ("फाल्गुन", "फाल्गुण"),
        ("चैत्र",),
    ),
    weekday_aliases=(
        ("सोमवार",),
        ("मंगलबार", "मङ्गलवार", "मंगलवार", "मंगल"),
        ("बुधवार",),
        ("बिहिबार", "बिहीवार", "बृहस्पतिबार", "बिहि"),
        ("शुक्रवार",),
        ("शनिवार",),
        ("आइतवार", "आईतबार"),
    ),
)
"""Nepali (Devanagari) month and weekday names with Devanagari digits."""

_BUILTIN = {EN.name: EN, NE.name: NE}


def get_locale(name: str) -> Locale:
    """Return a built-in locale by name.

    Args:
        name: ``"en"`` or ``"ne"`` (case-insensitive).

    Returns:
        The matching :class:`Locale`.

    Raises:
        LookupError: If no built-in locale has that name.
    """
    try:
        return _BUILTIN[name.lower()]
    except KeyError:
        message = f"unknown locale {name!r}; built-in locales are {sorted(_BUILTIN)}"
        raise LookupError(message) from None
