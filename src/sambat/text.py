"""Conversion between ASCII and Devanagari digits.

Devanagari digits are the Unicode code points U+0966 (०) through U+096F (९).
The conversion is exact and leaves every other character untouched.

Examples:
    >>> from sambat.text import to_ascii_digits, to_nepali_digits
    >>> to_nepali_digits("2083-06-15")
    '२०८३-०६-१५'
    >>> to_ascii_digits("२०८३ असोज १५")
    '2083 असोज 15'
"""

from __future__ import annotations

__all__ = ["ASCII_DIGITS", "DEVANAGARI_DIGITS", "to_ascii_digits", "to_nepali_digits"]

ASCII_DIGITS = "0123456789"
"""The ten ASCII digits, in value order."""

DEVANAGARI_DIGITS = "०१२३४५६७८९"
"""The ten Devanagari digits (U+0966..U+096F), in value order."""

_TO_DEVANAGARI = str.maketrans(ASCII_DIGITS, DEVANAGARI_DIGITS)
_TO_ASCII = str.maketrans(DEVANAGARI_DIGITS, ASCII_DIGITS)


def to_nepali_digits(text: str) -> str:
    """Replace every ASCII digit in ``text`` with its Devanagari digit.

    Args:
        text: Any string.

    Returns:
        The string with ``0``-``9`` replaced by ``०``-``९``.
    """
    return text.translate(_TO_DEVANAGARI)


def to_ascii_digits(text: str) -> str:
    """Replace every Devanagari digit in ``text`` with its ASCII digit.

    Args:
        text: Any string.

    Returns:
        The string with ``०``-``९`` replaced by ``0``-``9``.
    """
    return text.translate(_TO_ASCII)
