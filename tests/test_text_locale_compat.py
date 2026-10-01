from __future__ import annotations

import dataclasses
import datetime as dt

import pytest

from sambat import date, datetime
from sambat.compat import (
    from_datetime_date,
    from_datetime_datetime,
    to_datetime_date,
    to_datetime_datetime,
    translate_format,
)
from sambat.locale import ASCII_DIGITS, DEVANAGARI_DIGITS, EN, NE, Locale, get_locale
from sambat.text import to_ascii_digits, to_nepali_digits


def test_digit_conversion() -> None:
    assert to_nepali_digits("2083-06-15 abc") == "२०८३-०६-१५ abc"
    assert to_ascii_digits("२०८३ असोज १५") == "2083 असोज 15"
    assert to_ascii_digits(to_nepali_digits(ASCII_DIGITS)) == ASCII_DIGITS
    assert "".join(chr(0x966 + n) for n in range(10)) == DEVANAGARI_DIGITS


def test_builtin_locales() -> None:
    assert get_locale("EN") is EN
    assert get_locale("ne") is NE
    with pytest.raises(LookupError, match="unknown locale"):
        get_locale("fr")
    assert EN.month_spellings(6)[:2] == ("Ashwin", "Ash")
    assert "Asoj" in EN.month_spellings(6)
    assert "आश्विन" in NE.month_spellings(6)
    assert NE.weekday_spellings(3)[0] == "बिहीबार"
    assert NE.format_number("12") == "१२"
    assert EN.format_number("12") == "12"


def test_locale_validation() -> None:
    with pytest.raises(ValueError, match="month_names"):
        dataclasses.replace(EN, month_names=("x",))
    with pytest.raises(ValueError, match="digits"):
        dataclasses.replace(EN, digits="0123456788")
    custom = dataclasses.replace(EN, name="en-x", am_pm=("am", "pm"))
    assert isinstance(custom, Locale)
    assert datetime(2083, 1, 1, 13).strftime("%p", locale=custom) == "pm"


def test_compat_aliases_warn() -> None:
    with pytest.warns(DeprecationWarning, match="from_gregorian"):
        assert from_datetime_date(dt.date(2026, 10, 1)) == date(2083, 6, 15)
    with pytest.warns(DeprecationWarning, match="to_gregorian"):
        assert to_datetime_date(date(2083, 6, 15)) == dt.date(2026, 10, 1)
    with pytest.warns(DeprecationWarning, match=r"datetime\.from_gregorian"):
        value = from_datetime_datetime(dt.datetime(2026, 10, 1, 9))
    assert value == datetime(2083, 6, 15, 9)
    with pytest.warns(DeprecationWarning, match=r"datetime\.to_gregorian"):
        assert to_datetime_datetime(value) == dt.datetime(2026, 10, 1, 9)


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("%Y-%m-%d", "%Y-%m-%d", "2083-06-15"),
        ("%K-%n-%D", "%OY-%Om-%Od", "२०८३-०६-१५"),
        ("%G, %d %N %Y", "%A, %d %B %Y", "बिहीबार, 15 असोज 2083"),
        ("%k %h:%l:%s %i", "%Oy %OH:%OM:%OS %OI", "८३ ००:००:०० १२"),
        ("%A %B 100%%", "%A %B 100%%", "Thursday Ashwin 100%"),
    ],
)
def test_translate_format(old: str, new: str, expected: str) -> None:
    fmt, locale = translate_format(old)
    assert fmt == new
    assert date(2083, 6, 15).strftime(fmt, locale=locale) == expected


@pytest.mark.parametrize(
    ("old", "message"), [("%N %B", "mixes"), ("%Q", "no sambat"), ("%", "stray")]
)
def test_translate_format_errors(old: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        translate_format(old)
