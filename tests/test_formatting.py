from __future__ import annotations

import dataclasses
import datetime as dt

import pytest

from sambat import NEPAL_TZ, date, datetime
from sambat.locale import ASCII_DIGITS, EN, NE

VALUE = datetime(2083, 6, 15, 14, 5, 9, 1234, tzinfo=NEPAL_TZ)  # Thursday


@pytest.mark.parametrize(
    ("directive", "expected"),
    [
        ("%a", "Thu"),
        ("%A", "Thursday"),
        ("%b", "Ash"),
        ("%h", "Ash"),
        ("%B", "Ashwin"),
        ("%C", "20"),
        ("%d", "15"),
        ("%e", "15"),
        ("%f", "001234"),
        ("%G", "2083"),
        ("%H", "14"),
        ("%I", "02"),
        ("%j", "171"),
        ("%m", "06"),
        ("%M", "05"),
        ("%p", "PM"),
        ("%S", "09"),
        ("%u", "4"),
        ("%U", "24"),
        ("%V", "25"),
        ("%w", "4"),
        ("%W", "24"),
        ("%y", "83"),
        ("%Y", "2083"),
        ("%z", "+0545"),
        ("%:z", "+05:45"),
        ("%Z", "+0545"),
        ("%%", "%"),
        ("%n", "\n"),
        ("%t", "\t"),
        ("%D", "06/15/83"),
        ("%F", "2083-06-15"),
        ("%r", "02:05:09 PM"),
        ("%R", "14:05"),
        ("%T", "14:05:09"),
        ("%c", "Thu Ash 15 14:05:09 2083"),
        ("%x", "06/15/83"),
        ("%X", "14:05:09"),
    ],
)
def test_directives(directive: str, expected: str) -> None:
    assert VALUE.strftime(directive) == expected


def test_time_directives_match_stdlib() -> None:
    twin = VALUE.to_gregorian()
    for directive in ("%H", "%I", "%M", "%S", "%f", "%p", "%z", "%Z", "%%"):
        assert VALUE.strftime(directive) == twin.strftime(directive), directive


def test_twelve_hour_clock_edges() -> None:
    assert datetime(2083, 1, 1, 0).strftime("%I %p") == "12 AM"
    assert datetime(2083, 1, 1, 12).strftime("%I %p") == "12 PM"
    assert datetime(2083, 1, 1, 23).strftime("%I %p") == "11 PM"


def test_date_only_values_have_zero_time_and_no_zone() -> None:
    assert date(2083, 6, 5).strftime("%e|%H:%M:%S.%f|%z|%Z") == " 5|00:00:00.000000||"


def test_week_numbers_at_year_start() -> None:
    first = date(2083, 1, 1)  # Tuesday
    assert first.strftime("%j %U %W") == "001 00 00"


def test_offsets_with_seconds_and_negative() -> None:
    lmt = dt.datetime(1910, 1, 1, tzinfo=NEPAL_TZ)
    assert lmt.utcoffset() == dt.timedelta(hours=5, minutes=41, seconds=16)
    west = datetime(2083, 1, 1, tzinfo=dt.timezone(-dt.timedelta(hours=3, microseconds=5)))
    assert west.strftime("%z") == "-030000.000005"
    assert west.strftime("%:z") == "-03:00:00.000005"


def test_nepali_locale() -> None:
    assert VALUE.strftime("%A, %d %B %Y", locale=NE) == "बिहीबार, १५ असोज २०८३"
    assert VALUE.strftime("%p", locale=NE) == "अपराह्न"
    assert VALUE.strftime("%c", locale=NE) == "२०८३ असोज १५, बिहीबार १४:०५:०९"


def test_alternative_digits_modifier() -> None:
    assert VALUE.strftime("%OY-%Om-%Od %OH:%OM") == "२०८३-०६-१५ १४:०५"
    ascii_ne = dataclasses.replace(NE, digits=ASCII_DIGITS)
    assert VALUE.strftime("%d %B", locale=ascii_ne) == "15 असोज"


@pytest.mark.parametrize("fmt", ["%Q", "%", "%O", "%Oa", "%:", "%:x", "%E"])
def test_invalid_directives(fmt: str) -> None:
    with pytest.raises(ValueError, match="format"):
        VALUE.strftime(fmt)


def test_format_must_be_str() -> None:
    with pytest.raises(TypeError):
        VALUE.strftime(b"%Y")  # type: ignore[arg-type]


def test_default_locale_is_english() -> None:
    assert VALUE.strftime("%B") == VALUE.strftime("%B", locale=EN)
