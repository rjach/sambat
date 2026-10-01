from __future__ import annotations

import calendar as stdlib_calendar
import datetime as dt

import pytest

from sambat import calendar, date
from sambat.locale import NE


@pytest.fixture(autouse=True)
def _restore_first_weekday() -> object:
    yield
    calendar.setfirstweekday(calendar.MONDAY)


def test_constants() -> None:
    assert calendar.BAISHAKH == 1
    assert calendar.CHAITRA == 12
    assert calendar.MONDAY == 0
    assert calendar.SUNDAY == 6
    assert calendar.Month(6).name == "ASHWIN"
    assert calendar.month_name[6] == "Ashwin"
    assert calendar.month_abbr[0] == ""
    assert calendar.day_name[0] == "Monday"
    assert calendar.day_abbr[6] == "Sun"
    assert calendar.error is ValueError


def test_year_and_month_queries() -> None:
    assert calendar.monthrange(2083, 6) == (3, 31)
    assert calendar.days_in_month(2083, 3) == 32
    assert calendar.days_in_year(2081) == 366
    assert calendar.isleap(2081)
    assert not calendar.isleap(2083)
    assert calendar.leapdays(2075, 2084) == sum(
        1 for year in range(2075, 2084) if calendar.days_in_year(year) == 366
    )
    assert calendar.weekday(2083, 6, 15) == 3
    assert calendar.supported_range() == (1975, 2083)


def test_illegal_month_and_weekday() -> None:
    with pytest.raises(calendar.IllegalMonthError, match="bad month number 13"):
        calendar.monthrange(2083, 13)
    with pytest.raises(calendar.IllegalWeekdayError, match="bad weekday number 7"):
        calendar.setfirstweekday(7)
    assert issubclass(calendar.IllegalMonthError, ValueError)


def test_monthcalendar_and_iterators() -> None:
    weeks = calendar.monthcalendar(2083, 6)
    assert weeks[0] == [0, 0, 0, 1, 2, 3, 4]
    assert weeks[-1] == [26, 27, 28, 29, 30, 31, 0]
    cal = calendar.Calendar(calendar.SUNDAY)
    assert list(cal.iterweekdays()) == [6, 0, 1, 2, 3, 4, 5]
    days3 = list(cal.itermonthdays3(2083, 6))
    assert days3[0] == (2083, 5, 28)
    assert days3[-1] == (2083, 6, 31)
    days4 = list(cal.itermonthdays4(2083, 6))
    assert days4[0] == (2083, 5, 28, 6)
    dates = list(cal.itermonthdates(2083, 6))
    assert all(isinstance(value, date) for value in dates)
    assert len(dates) % 7 == 0
    assert cal.monthdatescalendar(2083, 6)[0][4] == date(2083, 6, 1)
    assert cal.getfirstweekday() == 6
    cal.setfirstweekday(8)
    assert cal.firstweekday == 1


def test_month_layout_matches_gregorian_weekdays() -> None:
    cal = calendar.Calendar()
    for day, weekday in cal.itermonthdays2(2083, 1):
        if day:
            assert date(2083, 1, day).to_gregorian().weekday() == weekday


def test_year_calendars() -> None:
    cal = calendar.Calendar()
    rows = cal.yeardayscalendar(2083, 4)
    assert len(rows) == 3
    assert len(rows[0]) == 4
    assert len(cal.yeardays2calendar(2083)) == 4
    assert cal.yeardatescalendar(2082, 6)[0][0][0][0].month in {12, 1}


def test_date_iterators_stop_at_the_supported_range() -> None:
    cal = calendar.Calendar()
    # Padding after Chaitra of the last supported year falls in an unpublished year.
    assert list(cal.itermonthdays3(2083, 12))[-1] == (2084, 1, 5)
    with pytest.raises(ValueError, match="out of range"):
        cal.monthdatescalendar(2083, 12)
    assert cal.monthdayscalendar(2083, 12)[-1][-1] == 0


def test_text_month() -> None:
    text = calendar.month(2083, 6)
    lines = text.splitlines()
    assert lines[0].strip() == "Ashwin 2083"
    assert lines[1] == "Mo Tu We Th Fr Sa Su"
    assert lines[2].endswith(" 1  2  3  4")
    assert calendar.TextCalendar().formatmonth(2083, 6, w=3, l=2).count("\n\n") > 0


def test_text_year() -> None:
    text = calendar.calendar(2083)
    assert text.splitlines()[0].strip() == "2083"
    assert "Baishakh" in text
    assert "Chaitra" in text


def test_print_functions(capsys: pytest.CaptureFixture[str]) -> None:
    calendar.prmonth(2083, 6)
    calendar.prcal(2083)
    calendar.prweek([(1, 0), (2, 1)], 2)
    calendar.format(["a", "b"], 3, 1)
    out = capsys.readouterr().out
    assert "Ashwin 2083" in out
    assert " a   b " in out


def test_module_level_first_weekday() -> None:
    calendar.setfirstweekday(calendar.SUNDAY)
    assert calendar.firstweekday() == 6
    assert calendar.weekheader(2) == "Su Mo Tu We Th Fr Sa"


def test_locale_text_calendar() -> None:
    cal = calendar.LocaleTextCalendar(calendar.SUNDAY, NE)
    text = cal.formatmonth(2083, 6)
    assert "असोज २०८३" in text
    assert "१५" in text
    assert cal.formatweekday(0, 9).strip() == "सोमबार"
    assert calendar.LocaleTextCalendar().locale.name == "en"


def test_dual_text_calendar() -> None:
    text = calendar.DualTextCalendar().formatmonth(2083, 6)
    lines = text.splitlines()
    assert lines[0].strip() == "Ashwin 2083 (Sep–Oct 2026)"
    assert lines[1].split() == ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    assert "15  1" in text  # Asoj 15 is 1 October
    chaitra = calendar.DualTextCalendar().formatmonth(2083, 9)
    assert "Dec 2026–Jan 2027" in chaitra


def test_html_calendar() -> None:
    html = calendar.HTMLCalendar().formatmonth(2083, 6)
    assert '<th colspan="7" class="month">Ashwin 2083</th>' in html
    assert '<td class="thu">1</td>' in html
    assert '<td class="noday">&nbsp;</td>' in html
    year = calendar.HTMLCalendar().formatyear(2083, width=4)
    assert year.count('<table border="0"') == 13
    page = calendar.HTMLCalendar().formatyearpage(2083, css=None)
    assert page.startswith(b"<!DOCTYPE html>")
    assert b"stylesheet" not in page
    styled = calendar.LocaleHTMLCalendar(locale=NE).formatyearpage(2083, encoding="ascii")
    assert b'href="calendar.css"' in styled
    assert b"&#" in styled  # Devanagari escaped for an ASCII page
    month_page = calendar.HTMLCalendar().formatmonthpage(2083, 6)
    assert b"<title>Calendar for BS 2083</title>" in month_page
    assert b"Ashwin 2083" in month_page
    assert calendar.standalone_month_name[6] == calendar.month_name[6]
    assert calendar.standalone_month_abbr[0] == ""


def test_dual_html_calendar() -> None:
    html = calendar.DualHTMLCalendar().formatmonth(2083, 6, withyear=False)
    assert '<td class="thu">15<span class="ad">1</span></td>' in html
    assert ">Ashwin<" in html


def test_timegm_matches_stdlib() -> None:
    value = (2083, 6, 15, 3, 45, 0)
    expected = stdlib_calendar.timegm(dt.datetime(2026, 10, 1, 3, 45).timetuple())
    assert calendar.timegm(value) == expected


def test_main_text(capsys: pytest.CaptureFixture[str]) -> None:
    assert calendar.main(["2083", "6"]) == 0
    assert "Ashwin 2083" in capsys.readouterr().out
    assert calendar.main(["2083", "6", "--dual", "-L", "ne"]) == 0
    assert "असोज" in capsys.readouterr().out
    assert calendar.main(["2083"]) == 0
    assert "Chaitra" in capsys.readouterr().out
    assert calendar.main(["2083", "--dual"]) == 0
    assert capsys.readouterr().out.count("2083 (") == 12


def test_main_html(capsys: pytest.CaptureFixture[str]) -> None:
    assert calendar.main(["2083", "6", "-t", "html"]) == 0
    assert capsys.readouterr().out.startswith("<table")
    assert calendar.main(["2083", "-t", "html", "--dual"]) == 0
    assert "<!DOCTYPE html>" in capsys.readouterr().out


def test_main_default_year(capsys: pytest.CaptureFixture[str]) -> None:
    assert calendar.main([]) == 0
    assert str(date.today().year) in capsys.readouterr().out


def test_main_errors(capsys: pytest.CaptureFixture[str]) -> None:
    assert calendar.main(["2100"]) == 1
    assert "out of range" in capsys.readouterr().err
    for args in (["2083", "13"], ["-f", "9"], ["-L", "fr"]):
        with pytest.raises(SystemExit):
            calendar.main(args)
