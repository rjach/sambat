# sambat

**Exact Bikram Sambat (Nepali calendar) dates with the full `datetime` API.**

`sambat.date` and `sambat.datetime` work like {class}`datetime.date` and
{class}`datetime.datetime`, with the year, month and day in the Bikram Sambat
(BS) calendar. The calendar-independent types (`timedelta`, `time`,
`timezone`, `tzinfo`, `UTC`) are the standard library's own objects.

```python
>>> import sambat
>>> d = sambat.date(2083, 6, 15)
>>> d.to_gregorian()
datetime.date(2026, 10, 1)
>>> d.strftime("%A, %d %B %Y")
'Thursday, 15 Ashwin 2083'
>>> d.weekday() == d.to_gregorian().weekday()
True

```

## Highlights

- **Exact, or an error.** Month lengths come from a table of officially
  published years; dates outside it raise instead of being guessed.
- **Real `datetime` parity**, checked by tests against the running Python:
  hashing, pickling, ISO 8601, `isocalendar`, `strptime`, `fold`, time zones,
  subclassing.
- **Nepali formatting and parsing**, in English or Devanagari.
- **BS calendar arithmetic**, periods and Nepal's **fiscal year**.
- **No dependencies**, fully typed, pure Python (CPython 3.11–3.15, free-threaded
  builds, PyPy).

## Installation

```console
$ pip install sambat
```

```{toctree}
:maxdepth: 2
:caption: Tutorial

tutorial
```

```{toctree}
:maxdepth: 1
:caption: How-to guides

how-to/migrate
how-to/storage
how-to/timezones
how-to/fiscal-year
how-to/calendar-data
```

```{toctree}
:maxdepth: 2
:caption: Reference

reference/api
reference/formatting
reference/parity
reference/cli
```

```{toctree}
:maxdepth: 1
:caption: Explanation

explanation/bikram-sambat
explanation/calendar-data
explanation/scope
```

```{toctree}
:maxdepth: 1
:caption: Project

changelog
GitHub <https://github.com/rjach/sambat>
PyPI <https://pypi.org/project/sambat/>
```
