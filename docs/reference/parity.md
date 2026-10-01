# Parity with `datetime` and `calendar`

`sambat.date`, `sambat.datetime` and `sambat.calendar` implement every public
name of the running Python's {mod}`datetime` and {mod}`calendar` modules. The
test suite enforces this: when a new Python version adds a public name, the
parity tests fail until sambat implements it or it is listed below.

## Shared with the standard library

- `sambat.timedelta`, `time`, `timezone`, `tzinfo` and `UTC` are the standard
  library objects themselves.
- `toordinal()`, `weekday()`, `isoweekday()`, `timestamp()`, hashing and
  arithmetic agree exactly with the Gregorian equivalent.
- Error types and most error messages match CPython.
- Methods added in newer Pythons are available on every supported version:
  `date.strptime` (3.14), `__replace__` / `copy.replace` (3.13) and the broad
  `fromisoformat` grammar (3.11).

## Intentional differences

Separate types
: `sambat.date` does not subclass {class}`datetime.date`. A BS date never
  compares equal to a Gregorian date, and ordering or subtracting across the
  two raises `TypeError`. Convert explicitly with `to_gregorian()` and
  `from_gregorian()`.

Supported range
: `MINYEAR` and `MAXYEAR` come from the calendar table. Constructors raise
  `ValueError` outside it; arithmetic raises `OverflowError`, as the standard
  library does at its limits.

ISO weeks
: `isocalendar()`, `fromisocalendar()`, `%G`, `%V` and ISO week strings use a
  BS week calendar: Monday-start weeks, week 1 contains the first Thursday of
  the BS year. The Gregorian ISO week is `to_gregorian().isocalendar()`. For the
  first days of `MINYEAR` the week-year is not representable and
  `isocalendar()` raises `ValueError`.

`timetuple()`
: Returns BS fields (`tm_yday` is the day of the BS year). Do not pass it to
  {func}`time.mktime`.

`strftime` and `strptime`
: Pure Python with a fixed directive set, a `locale` keyword and the `%O`
  modifier; unknown directives raise `ValueError`. See {doc}`formatting`.

`ctime()`
: Uses English BS month abbreviations, e.g. `Thu Ash 15 14:05:09 2083`.

Time zones
: `tzinfo` methods are always called with the equivalent standard-library
  datetime, never with a `sambat.datetime`.

`utcnow()` and `utcfromtimestamp()`
: Emit `DeprecationWarning` on every Python version (they are deprecated
  since Python 3.12).

`sambat.calendar`
: - BS month constants (`BAISHAKH` … `CHAITRA`) replace `JANUARY` … `DECEMBER`.
  - `isleap(year)` means "has 366 days"; there is no leap rule in BS.
  - `LocaleTextCalendar` and `LocaleHTMLCalendar` take a sambat `Locale`
    instead of a C locale name, and `different_locale` is not provided.
  - Iterators that yield date objects (`itermonthdates`, `monthdatescalendar`,
    …) raise `ValueError` when a padding day falls outside the supported range,
    just as the standard library does at year 9999.
