# Report by Nepal's fiscal year

The Government of Nepal's fiscal year starts on Shrawan 1. {mod}`sambat.fiscal`
models the year and its standard subdivisions.

```python
>>> from sambat import date
>>> from sambat.fiscal import FiscalYear
>>> fy = FiscalYear.of(date(2082, 10, 5))
>>> fy, fy.label_ne
(FiscalYear(2082), '२०८२/८३')
>>> fy.start, fy.end
(sambat.date(2082, 4, 1), sambat.date(2083, 3, 32))

```

## Subdivisions

| Method | Periods | Months |
|---|---|---|
| `quarter(n)` / `quarter_of(d)` | 4 quarters (त्रैमासिक) | Shrawan–Asoj, Kartik–Poush, Magh–Chaitra, Baishakh–Asar |
| `chaumasik(n)` / `chaumasik_of(d)` | 3 four-month periods (चौमासिक) | Shrawan–Kartik, Mangsir–Falgun, Chaitra–Asar |
| `half(n)` / `half_of(d)` | 2 halves (अर्धवार्षिक) | Shrawan–Poush, Magh–Asar |

```python
>>> fy.quarter(3)
Period(sambat.date(2082, 10, 1), sambat.date(2082, 12, 30))
>>> fy.chaumasik_of(date(2082, 10, 5))
2
>>> [str(month.start) for month in fy.months()][:3]
['2082-04-01', '2082-05-01', '2082-06-01']

```

## Labels

```python
>>> FiscalYear.from_label("२०८२/८३") == FiscalYear.from_label("2082-2083") == fy
True

```

## Fiscal years beyond the published calendar

A fiscal year that ends after {data}`sambat.MAXYEAR` can be created, and its
earlier parts queried. Boundaries that fall in an unpublished BS year raise
`ValueError`:

```python
>>> current = FiscalYear(2083)
>>> current.quarter(1)
Period(sambat.date(2083, 4, 1), sambat.date(2083, 6, 31))
>>> current.end
Traceback (most recent call last):
    ...
ValueError: year 2084 is out of range; sambat supports BS 1975..2083 (later years had no officially published calendar when this version of sambat was released; upgrading sambat may add them)

```

Organisations with a different financial year can pass `start_month`, for
example `FiscalYear.of(d, start_month=1)` for a Baishakh–Chaitra year.
