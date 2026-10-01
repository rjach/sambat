"""The ``sambat`` command line interface.

Run ``sambat --help`` (or ``python -m sambat --help``) for usage. Every
command accepts ``--json`` for machine-readable output. Unlike the library,
the CLI defaults to Nepal time and Sunday-first weeks.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from typing import TYPE_CHECKING, Any

from sambat import MAXYEAR, MINYEAR, NEPAL_TZ, __version__, today_np
from sambat import calendar as bs_calendar
from sambat._date import date
from sambat._datetime import datetime
from sambat.delta import diff
from sambat.fiscal import FiscalYear
from sambat.locale import EN, Locale, get_locale

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

_WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def _emit(options: argparse.Namespace, text: str, payload: dict[str, Any]) -> None:
    if options.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(text)


def _describe(value: date, locale: Locale) -> dict[str, Any]:
    return {
        "bs": value.isoformat(),
        "ad": value.to_gregorian().isoformat(),
        "weekday": value.strftime("%A", locale=locale),
        "text": value.strftime("%A, %d %B %Y", locale=locale),
    }


def _parse_bs(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parse_ad(text: str) -> _dt.date:
    try:
        return _dt.date.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _cmd_today(options: argparse.Namespace) -> int:
    now = datetime.now(NEPAL_TZ)
    today = today_np()
    info = _describe(today, options.locale)
    info["time"] = now.strftime("%H:%M:%S", locale=options.locale)
    info["timezone"] = "Asia/Kathmandu"
    _emit(options, f"{info['text']}  ({info['bs']} BS = {info['ad']} AD)", info)
    return 0


def _cmd_convert(options: argparse.Namespace) -> int:
    if options.to_bs:
        value = date.from_gregorian(_parse_ad(options.date))
    else:
        value = _parse_bs(options.date)
    info = _describe(value, options.locale)
    text = (
        f"{info['ad']} AD = {info['bs']} BS ({info['text']})"
        if options.to_bs
        else f"{info['bs']} BS = {info['ad']} AD ({info['text']})"
    )
    _emit(options, text, info)
    return 0


def _cmd_cal(options: argparse.Namespace) -> int:
    year = options.year if options.year is not None else today_np().year
    first = _WEEKDAYS[options.first_weekday]
    if options.dual:
        cal: bs_calendar.LocaleTextCalendar = bs_calendar.DualTextCalendar(first, options.locale)
    else:
        cal = bs_calendar.LocaleTextCalendar(first, options.locale)
    months = [options.month] if options.month is not None else list(range(1, 13))
    if options.json:
        payload = {
            "year": year,
            "months": [
                {
                    "month": number,
                    "name": options.locale.month_names[number - 1],
                    "days": bs_calendar.days_in_month(year, number),
                    "weeks": [
                        [str(day) if day.month == number else None for day in week]
                        for week in cal.monthdatescalendar(year, number)
                    ],
                }
                for number in months
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if options.month is not None or options.dual:
        print("\n".join(cal.formatmonth(year, number) for number in months), end="")
    else:
        print(cal.formatyear(year), end="")
    return 0


def _cmd_fy(options: argparse.Namespace) -> int:
    value = _parse_bs(options.date) if options.date else today_np()
    fy = FiscalYear.of(value)
    parts: list[tuple[str, int, Callable[[int], Any]]] = [
        ("quarter", 4, fy.quarter),
        ("chaumasik", 3, fy.chaumasik),
        ("half", 2, fy.half),
    ]
    payload: dict[str, Any] = {
        "fiscal_year": fy.label,
        "start": fy.start.isoformat(),
        "date": value.isoformat(),
        "fiscal_month": fy.fiscal_month(value),
        "quarter": fy.quarter_of(value),
        "chaumasik": fy.chaumasik_of(value),
        "half": fy.half_of(value),
    }
    lines = [
        f"Fiscal year {fy.label} (starts {fy.start} BS)",
        (
            f"{value} BS is in month {payload['fiscal_month']}, quarter {payload['quarter']}, "
            f"chaumasik {payload['chaumasik']}, half {payload['half']}"
        ),
    ]
    for name, count, getter in parts:
        if not getattr(options, name):
            continue
        periods: list[dict[str, int | str | None]] = []
        for number in range(1, count + 1):
            try:
                period = getter(number)
            except ValueError:
                periods.append({"number": number, "start": None, "end": None})
                lines.append(f"  {name} {number}: beyond the supported calendar range")
                continue
            periods.append({"number": number, "start": str(period.start), "end": str(period.end)})
            lines.append(f"  {name} {number}: {period.start} .. {period.end} ({period.days} days)")
        payload[f"{name}s"] = periods
    _emit(options, "\n".join(lines), payload)
    return 0


def _cmd_diff(options: argparse.Namespace) -> int:
    start, end = _parse_bs(options.start), _parse_bs(options.end)
    delta = diff(start, end)
    days = (end - start).days
    payload = {"years": delta.years, "months": delta.months, "days": delta.days, "total_days": days}
    text = f"{delta.years} years, {delta.months} months, {delta.days} days ({days} days in total)"
    _emit(options, text, payload)
    return 0


def _cmd_range(options: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "min_year": MINYEAR,
        "max_year": MAXYEAR,
        "min_date": str(date.min),
        "max_date": str(date.max),
        "min_ad": str(date.min.to_gregorian()),
        "max_ad": str(date.max.to_gregorian()),
    }
    text = (
        f"BS {MINYEAR}..{MAXYEAR} "
        f"({payload['min_date']} = {payload['min_ad']} AD to "
        f"{payload['max_date']} = {payload['max_ad']} AD)"
    )
    _emit(options, text, payload)
    return 0


def _locale_argument(name: str) -> Locale:
    try:
        return get_locale(name)
    except LookupError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the ``sambat`` command."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="print JSON")
    common.add_argument("--locale", type=_locale_argument, default=EN, help="en (default) or ne")

    parser = argparse.ArgumentParser(
        prog="sambat", description="Bikram Sambat (Nepali calendar) dates on the command line."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    today = commands.add_parser("today", parents=[common], help="today's date in Nepal")
    today.set_defaults(handler=_cmd_today)

    convert = commands.add_parser("convert", parents=[common], help="convert BS <-> AD")
    convert.add_argument("date", help="YYYY-MM-DD (BS, or AD with --to-bs)")
    convert.add_argument("--to-bs", action="store_true", help="the input is an AD date")
    convert.set_defaults(handler=_cmd_convert)

    cal = commands.add_parser("cal", parents=[common], help="print a month or year calendar")
    cal.add_argument("year", nargs="?", type=int, help="BS year (default: this year)")
    cal.add_argument("month", nargs="?", type=int, choices=range(1, 13), metavar="month")
    cal.add_argument("--dual", action="store_true", help="show AD day numbers too")
    cal.add_argument(
        "--first-weekday", choices=sorted(_WEEKDAYS), default="sun", help="default: sun"
    )
    cal.set_defaults(handler=_cmd_cal)

    fy = commands.add_parser("fy", parents=[common], help="Nepal fiscal year of a BS date")
    fy.add_argument("date", nargs="?", help="BS date YYYY-MM-DD (default: today)")
    fy.add_argument("--quarters", dest="quarter", action="store_true", help="list quarters")
    fy.add_argument("--chaumasik", dest="chaumasik", action="store_true", help="list chaumasik")
    fy.add_argument("--halves", dest="half", action="store_true", help="list halves")
    fy.set_defaults(handler=_cmd_fy)

    difference = commands.add_parser("diff", parents=[common], help="years, months, days between")
    difference.add_argument("start", help="BS date YYYY-MM-DD")
    difference.add_argument("end", help="BS date YYYY-MM-DD")
    difference.set_defaults(handler=_cmd_diff)

    supported = commands.add_parser("range", parents=[common], help="supported BS range")
    supported.set_defaults(handler=_cmd_range)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name (defaults to ``sys.argv[1:]``).

    Returns:
        The process exit status.
    """
    parser = build_parser()
    options = parser.parse_args(argv)
    try:
        status: int = options.handler(options)
    except (ValueError, argparse.ArgumentTypeError) as exc:
        print(f"sambat: error: {exc}", file=sys.stderr)
        return 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
