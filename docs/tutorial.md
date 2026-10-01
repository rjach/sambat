# Tutorial

This tutorial walks through the everyday tasks: creating BS dates, converting
to and from the Gregorian calendar, formatting in English and Nepali,
arithmetic, and time zones.

## Creating dates

`sambat.date` takes a BS year, month (1 = Baishakh … 12 = Chaitra) and day.
Months have 29 to 32 days, so `day=32` is valid in long months:

```python
>>> from sambat import date
>>> date(2083, 3, 32)
sambat.date(2083, 3, 32)
>>> date(2083, 3, 32).days_in_month()
32
>>> date(2083, 4, 32)
Traceback (most recent call last):
    ...
ValueError: day must be in 1..31 for BS 2083-04, not 32

```

Dates outside the published calendar raise `ValueError` with an explanation:

```python
>>> import sambat
>>> sambat.MINYEAR, sambat.MAXYEAR
(1975, 2083)
>>> date(2090, 1, 1)
Traceback (most recent call last):
    ...
ValueError: year 2090 is out of range; sambat supports BS 1975..2083 (later years had no officially published calendar when this version of sambat was released; upgrading sambat may add them)

```

## Converting

```python
>>> import datetime
>>> date.from_gregorian(datetime.date(2026, 4, 14))
sambat.date(2083, 1, 1)
>>> date(2083, 1, 1).to_gregorian()
datetime.date(2026, 4, 14)

```

`toordinal()` returns the same day number as the standard library, so you can
also convert through ordinals:

```python
>>> date.fromordinal(datetime.date(2026, 10, 1).toordinal())
sambat.date(2083, 6, 15)

```

## Today

`date.today()` and `datetime.now()` use the machine's local time zone, exactly
like the standard library. On a server running in UTC that can be the wrong
day for Nepal, so sambat provides explicit helpers:

```python
>>> today = sambat.today_np()  # the current date in Asia/Kathmandu
>>> now = sambat.now_np()      # an aware datetime in Asia/Kathmandu
>>> now.tzinfo
sambat.NEPAL_TZ

```

## Formatting

`strftime` supports the usual directives, with BS meanings for the date ones:

```python
>>> d = date(2083, 6, 15)
>>> d.strftime("%Y-%m-%d (%A, %B %d)")
'2083-06-15 (Thursday, Ashwin 15)'
>>> d.strftime("day %j of the year, week %V")
'day 171 of the year, week 25'

```

Pass `locale=NE` for Devanagari names and digits:

```python
>>> from sambat.locale import NE
>>> d.strftime("%Y साल %B %d गते, %A", locale=NE)
'२०८३ साल असोज १५ गते, बिहीबार'

```

The `%O` modifier renders any numeric field with Devanagari digits, whatever
the locale:

```python
>>> d.strftime("%OY/%Om/%Od")
'२०८३/०६/१५'

```

See {doc}`reference/formatting` for every directive.

## Parsing

```python
>>> date.fromisoformat("2083-06-15")
sambat.date(2083, 6, 15)
>>> date.strptime("15 Asoj 2083", "%d %B %Y")
sambat.date(2083, 6, 15)
>>> date.strptime("२०८३ आश्विन १५", "%Y %B %d", locale=NE)
sambat.date(2083, 6, 15)

```

Parsing accepts ASCII and Devanagari digits and the common spellings of each
month (`Ashwin`, `Asoj`, `Aswin`, `असोज`, `आश्विन`, …).

## Arithmetic

Adding a `timedelta` works exactly as with the standard library:

```python
>>> d + datetime.timedelta(days=17)
sambat.date(2083, 7, 1)
>>> date(2083, 7, 1) - date(2083, 1, 1)
datetime.timedelta(days=187)

```

For calendar months and years, use {mod}`sambat.delta`:

```python
>>> from sambat.delta import relativedelta, diff
>>> date(2083, 3, 32) + relativedelta(months=1)  # clamped: Shrawan has 31 days
sambat.date(2083, 4, 31)
>>> diff(date(2056, 4, 12), date(2083, 6, 15))
relativedelta(years=+27, months=+2, days=+3)

```

## Date and time with time zones

`sambat.datetime` accepts any `tzinfo`. `sambat.NEPAL_TZ` models Nepal's
offset history without needing the `tzdata` package:

```python
>>> from sambat import NEPAL_TZ, datetime as bs_datetime
>>> meeting = bs_datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ)
>>> meeting.isoformat()
'2083-06-15T09:30:00+05:45'
>>> meeting.astimezone(sambat.UTC)
sambat.datetime(2083, 6, 15, 3, 45, tzinfo=datetime.timezone.utc)

```

## Calendars

{mod}`sambat.calendar` mirrors the standard library's {mod}`calendar` module:

```python
>>> from sambat import calendar
>>> print(calendar.month(2083, 6))
    Ashwin 2083
Mo Tu We Th Fr Sa Su
          1  2  3  4
 5  6  7  8  9 10 11
12 13 14 15 16 17 18
19 20 21 22 23 24 25
26 27 28 29 30 31
<BLANKLINE>

```

`DualTextCalendar` prints the Gregorian day next to each BS day, the way
Nepali wall calendars do. The command line exposes it as `sambat cal --dual`.
