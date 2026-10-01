# sambat

[![PyPI](https://img.shields.io/pypi/v/sambat.svg)](https://pypi.org/project/sambat/)
[![Python versions](https://img.shields.io/pypi/pyversions/sambat.svg)](https://pypi.org/project/sambat/)
[![CI](https://github.com/rjach/sambat/actions/workflows/ci.yml/badge.svg)](https://github.com/rjach/sambat/actions/workflows/ci.yml)
[![Docs](https://github.com/rjach/sambat/actions/workflows/docs.yml/badge.svg)](https://rjach.github.io/sambat/)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/rjach/sambat/badge)](https://scorecard.dev/viewer/?uri=github.com/rjach/sambat)
[![License](https://img.shields.io/pypi/l/sambat.svg)](https://github.com/rjach/sambat/blob/main/LICENSE)

**Exact Bikram Sambat (Nepali calendar) dates with the full `datetime` API.**

`sambat.date` and `sambat.datetime` work like `datetime.date` and
`datetime.datetime`, with the year, month and day in the Bikram Sambat (BS)
calendar. They have the same constructors, methods, operators and error types.
The calendar-independent types (`timedelta`, `time`, `timezone`, `tzinfo`, `UTC`)
*are* the standard library's own objects.

```python
>>> import sambat
>>> d = sambat.date(2083, 6, 15)
>>> d.to_gregorian()
datetime.date(2026, 10, 1)
>>> d.strftime("%A, %d %B %Y")
'Thursday, 15 Ashwin 2083'
>>> d + sambat.timedelta(days=17)
sambat.date(2083, 7, 1)
>>> sambat.date.from_gregorian(sambat.date.max.to_gregorian())
sambat.date(2083, 12, 30)

```

## Why sambat

- **Exact, or an error.** BS month lengths (29–32 days) are decided and
  published by Nepal's calendar committee; no formula reproduces them. sambat
  ships a table of officially published years only. Dates outside that range
  raise `ValueError` instead of being guessed. Each row of the table records
  how it was verified (see [Calendar data](#calendar-data)).
- **Real `datetime` parity.** Hashing, pickling, `copy.replace`, ISO 8601
  (`fromisoformat`, week dates, every `timespec`), `isocalendar`, `strptime`,
  `fold`, `astimezone`, timestamps, subclassing: the behaviour matches CPython
  and is enforced by tests that compare against the running Python.
- **Same day numbers as the standard library.** `toordinal()` returns the
  stdlib ordinal, so weekdays and arithmetic agree with the Gregorian date.
- **Any time zone.** `zoneinfo`, `dateutil` and `pytz` work unchanged.
  `sambat.NEPAL_TZ` models Nepal's full offset history (LMT, +05:30 until 1986,
  +05:45 since) without needing `tzdata`.
- **Nepali formatting.** English and Devanagari month and weekday names,
  Devanagari digits, and parsing that accepts both scripts and common
  spellings (`Asoj`, `Ashwin`, `आश्विन`…).
- **Nepal-specific helpers.** BS month arithmetic (`relativedelta`), month and
  year periods, and Nepal's fiscal year with quarters and chaumasik periods.
- **No dependencies, fully typed, pure Python.** Works on CPython 3.11–3.15,
  free-threaded builds and PyPy.

## Installation

```console
pip install sambat
```

## Usage

### Converting

```python
>>> import datetime
>>> from sambat import date, datetime as bs_datetime, NEPAL_TZ
>>> date.from_gregorian(datetime.date(2026, 4, 14))
sambat.date(2083, 1, 1)
>>> date(2083, 1, 1).to_gregorian()
datetime.date(2026, 4, 14)
>>> bs_datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ).isoformat()
'2083-06-15T09:30:00+05:45'

```

`sambat.today_np()` and `sambat.now_np()` return the current date and time in
Nepal, whatever the machine's time zone. `date.today()` and `datetime.now()`
behave exactly like the standard library (machine-local time).

### Formatting and parsing in Nepali

```python
>>> from sambat.locale import NE
>>> d = date(2083, 6, 15)
>>> d.strftime("%Y साल %B %d गते, %A", locale=NE)
'२०८३ साल असोज १५ गते, बिहीबार'
>>> d.strftime("%OY-%Om-%Od")  # %O: Devanagari digits in any locale
'२०८३-०६-१५'
>>> date.strptime("२०८३ आश्विन १५", "%Y %B %d", locale=NE)
sambat.date(2083, 6, 15)

```

### Month arithmetic, periods and the fiscal year

```python
>>> from sambat.delta import relativedelta, diff
>>> date(2083, 3, 32) + relativedelta(months=1)  # Shrawan has 31 days
sambat.date(2083, 4, 31)
>>> diff(date(2056, 4, 12), date(2083, 6, 15))  # an age
relativedelta(years=+27, months=+2, days=+3)
>>> from sambat.fiscal import FiscalYear
>>> fy = FiscalYear.of(date(2083, 6, 15))
>>> fy.label, fy.start, fy.quarter_of(date(2083, 6, 15))
('2083/84', sambat.date(2083, 4, 1), 1)

```

### Calendars

```console
$ sambat cal 2083 6 --dual
        Ashwin 2083 (Sep–Oct 2026)
 Sun   Mon   Tue   Wed   Thu   Fri   Sat
                         1 17  2 18  3 19
 4 20  5 21  6 22  7 23  8 24  9 25 10 26
11 27 12 28 13 29 14 30 15  1 16  2 17  3
18  4 19  5 20  6 21  7 22  8 23  9 24 10
25 11 26 12 27 13 28 14 29 15 30 16 31 17
```

`sambat.calendar` mirrors the standard library's `calendar` module
(`monthrange`, `monthcalendar`, `TextCalendar`, `HTMLCalendar`…). The `sambat`
command also offers `today`, `convert`, `fy`, `diff` and `range`; all of them
accept `--json`.

## Calendar data

The month lengths live in [`data/calendar.csv`](data/calendar.csv), one row per
BS year. The package currently supports **BS 1975–2083** (13 April 1918 – 13
April 2027). Every row records its evidence:

| Evidence | Meaning |
|---|---|
| `verified` | Checked month by month against a published panchang: the national panchang of the Nepal Panchanga Nirnayak Bikas Samiti (Government of Nepal) for 2082–2083, and the Surya Panchanga for 2081. |
| `consensus` | At least five independent open-source tables cover the year, and at most one disagrees. |
| `disputed` | Open-source tables disagree (5 years). The value follows the majority or a documented upstream correction, and each dispute is listed in [`data/README.md`](data/README.md). |

Rows are only ever added for years whose official calendar has been
published. When the committee publishes a new year, a release adds one row.
See [the data documentation](https://rjach.github.io/sambat/explanation/calendar-data.html)
and [CONTRIBUTING.md](CONTRIBUTING.md) to help verify rows against primary
sources.

## Documentation

Full documentation, including the API reference, the parity notes and a
migration guide from `nepali-datetime`, is at **https://rjach.github.io/sambat/**.

## Contributing

Bug reports, calendar verifications and pull requests are welcome. Please read
[CONTRIBUTING.md](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md).
Report security issues privately as described in [SECURITY.md](SECURITY.md).

## Acknowledgements

sambat is a clean-room implementation. The open-source BS converters listed in
[`data/sources.toml`](data/sources.toml), in particular
[nepali-datetime](https://github.com/amitgaru/nepali-datetime), were used to
cross-check the calendar table.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
