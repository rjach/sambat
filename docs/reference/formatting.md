# Format directives

`strftime` and `strptime` are implemented in pure Python with the same
directive set on every platform. Unknown directives raise `ValueError` (the
standard library passes them to the C library, which varies by platform).

## Directives

| Directive | Meaning | Example (`2083-06-15 14:05:09`) |
|---|---|---|
| `%a` | Abbreviated weekday | `Thu` |
| `%A` | Full weekday | `Thursday` |
| `%b`, `%h` | Abbreviated BS month | `Ash` |
| `%B` | Full BS month | `Ashwin` |
| `%C` | Century | `20` |
| `%d` | Day of the month (01–32) | `15` |
| `%e` | Day of the month, space-padded | `15` |
| `%f` | Microsecond (000000–999999) | `000000` |
| `%G` | BS week-numbering year (see {meth}`sambat.date.isocalendar`) | `2083` |
| `%H` | Hour (00–23) | `14` |
| `%I` | Hour (01–12) | `02` |
| `%j` | Day of the BS year (001–366) | `171` |
| `%m` | BS month (01–12) | `06` |
| `%M` | Minute | `05` |
| `%p` | AM/PM | `PM` |
| `%S` | Second | `09` |
| `%u` | Weekday, Monday = 1 … Sunday = 7 | `4` |
| `%U` | Week of the BS year, weeks starting Sunday (00–53) | `24` |
| `%V` | BS week number (01–53) | `25` |
| `%w` | Weekday, Sunday = 0 … Saturday = 6 | `4` |
| `%W` | Week of the BS year, weeks starting Monday (00–53) | `24` |
| `%y` | Year without century; parsed as 2000 + yy | `83` |
| `%Y` | BS year, at least four digits | `2083` |
| `%z` | UTC offset `+HHMM[SS[.ffffff]]` (empty if naive) | `+0545` |
| `%:z` | UTC offset `+HH:MM[:SS[.ffffff]]` | `+05:45` |
| `%Z` | Time zone name (empty if naive) | `+0545` |
| `%c` | Locale date and time | `Thu Ash 15 14:05:09 2083` |
| `%x` | Locale date | `06/15/83` |
| `%X` | Locale time | `14:05:09` |
| `%D` | `%m/%d/%y` | `06/15/83` |
| `%F` | `%Y-%m-%d` | `2083-06-15` |
| `%r` | `%I:%M:%S %p` | `02:05:09 PM` |
| `%R` | `%H:%M` | `14:05` |
| `%T` | `%H:%M:%S` | `14:05:09` |
| `%n`, `%t`, `%%` | Newline, tab, `%` | |

## Devanagari digits: `%O`

`%O` before any numeric directive (`%OY`, `%Od`, `%OH`, …) renders that field
with Devanagari digits, whatever the locale. This follows the POSIX meaning of
`%O` ("alternative digits").

## Locales

`strftime`, `strptime` and the `Locale*Calendar` classes take an explicit
{class}`~sambat.locale.Locale`. The built-in locales are
{data}`~sambat.locale.EN` (English names, ASCII digits; the default) and
{data}`~sambat.locale.NE` (Devanagari names and digits). The process C locale
is never consulted.

| | `EN` | `NE` |
|---|---|---|
| Months | Baishakh, Jestha, Asar, Shrawan, Bhadra, Ashwin, Kartik, Mangsir, Poush, Magh, Falgun, Chaitra | बैशाख, जेठ, असार, साउन, भदौ, असोज, कात्तिक, मंसिर, पुस, माघ, फागुन, चैत |
| Weekdays (Monday first) | Monday … Sunday | सोमबार, मङ्गलबार, बुधबार, बिहीबार, शुक्रबार, शनिबार, आइतबार |
| `%p` | AM, PM | पूर्वाह्न, अपराह्न |
| `%c` | `%a %b %e %H:%M:%S %Y` | `%Y %B %d, %A %H:%M:%S` |
| `%x` | `%m/%d/%y` | `%Y/%m/%d` |

Create variants with {func}`dataclasses.replace`, for example Nepali names
with ASCII digits:

```python
>>> import dataclasses
>>> from sambat import date
>>> from sambat.locale import NE, ASCII_DIGITS
>>> date(2083, 6, 15).strftime("%d %B %Y", locale=dataclasses.replace(NE, digits=ASCII_DIGITS))
'15 असोज 2083'

```

## Parsing rules

- Numbers may use ASCII or Devanagari digits.
- Month and weekday names are matched case-insensitively against the locale's
  names and its documented alternative spellings
  (`Locale.month_aliases`, `Locale.weekday_aliases`).
- `%y` means 2000 + yy.
- Without a year the result is in BS 2000; parsing a day of the month without
  a year emits `DeprecationWarning`, as Python 3.13+ does.
- Composite directives (`%c`, `%x`, `%X`, `%D`, `%F`, `%r`, `%R`, `%T`) expand
  to their templates.
