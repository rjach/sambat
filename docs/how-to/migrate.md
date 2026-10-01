# Migrate from nepali-datetime

sambat is a clean-room replacement for
[nepali-datetime](https://github.com/amitgaru/nepali-datetime). Most code
needs only a few changes, but some behaviour differs on purpose because sambat
follows the standard library exactly.

## API mapping

| nepali-datetime | sambat |
|---|---|
| `import nepali_datetime` | `import sambat` |
| `nepali_datetime.date(2083, 6, 15)` | `sambat.date(2083, 6, 15)` |
| `date.from_datetime_date(d)` | `date.from_gregorian(d)` |
| `d.to_datetime_date()` | `d.to_gregorian()` |
| `datetime.from_datetime_datetime(dt)` | `datetime.from_gregorian(dt)` |
| `dt.to_datetime_datetime()` | `dt.to_gregorian()` |
| `d.calendar()` (prints with ANSI colours) | `sambat.calendar.DualTextCalendar().formatmonth(...)` or `sambat cal` |
| `nepali_datetime.UTC0545` | `sambat.NEPAL_TZ` (with the full offset history) |

The old conversion names are available as deprecated functions in
{mod}`sambat.compat`, which emit `DeprecationWarning`.

## Behaviour changes

`weekday()` starts on Monday
: nepali-datetime returned Sunday = 0. sambat returns Monday = 0 like
  `datetime.date.weekday()`; use `isoweekday()` or `(d.weekday() + 1) % 7`
  for Sunday-based numbering.

`toordinal()` matches the standard library
: nepali-datetime counted days from BS 1975-01-01. sambat returns the
  proleptic Gregorian ordinal, so `d.toordinal() == d.to_gregorian().toordinal()`.

`now()` and `today()` use local time
: nepali-datetime always used Nepal time. sambat follows the standard library
  (machine-local time); use `sambat.now_np()` and `sambat.today_np()` for
  Nepal time.

Years after the last published calendar raise
: nepali-datetime shipped projected month lengths up to BS 2100. sambat only
  ships published years, so later dates raise `ValueError` until a release
  adds them.

`isocalendar()`, hashing and pickling work
: They were missing or broken in nepali-datetime.

## Format strings

nepali-datetime used custom `strftime` letters that collide with standard
directives (`%D`, `%n`, `%G`, `%h`, `%k`, `%l`, `%s`, `%N`, `%K`). sambat uses
the standard directives with a `locale` and the `%O` (Devanagari digits)
modifier instead. {func}`sambat.compat.translate_format` converts old format
strings:

```python
>>> from sambat import date
>>> from sambat.compat import translate_format
>>> fmt, locale = translate_format("%K %N %D, %G")
>>> fmt
'%OY %B %Od, %A'
>>> date(2083, 6, 15).strftime(fmt, locale=locale)
'२०८३ असोज १५, बिहीबार'

```

## Calendar differences

sambat's table differs from nepali-datetime's in a few rows. BS 2082 and 2083
have been verified against the national panchang, and every disputed year is
documented in {doc}`../explanation/calendar-data`. If you stored BS dates
produced by nepali-datetime for years after 2083, they were projections; they
will need checking once the official calendar for those years is published.
