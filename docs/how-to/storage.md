# Store dates in databases and APIs

sambat deliberately does not subclass {class}`datetime.date`. Database
drivers, ORMs and serialisers would otherwise read Gregorian values at the C
level and BS values in Python, silently corrupting data. Convert explicitly at
the boundary instead.

## Databases

Store the Gregorian equivalent in an ordinary `DATE` or `TIMESTAMP` column, so
sorting, indexing and database date functions keep working, and convert when
reading:

```python
>>> import datetime
>>> from sambat import date
>>> row_value = date(2083, 6, 15).to_gregorian()  # write this
>>> row_value
datetime.date(2026, 10, 1)
>>> date.from_gregorian(row_value)  # read back
sambat.date(2083, 6, 15)

```

For aware datetimes, `sambat.datetime.to_gregorian()` keeps the `tzinfo` and
`fold`.

## JSON and HTTP APIs

`isoformat()` and `fromisoformat()` round-trip exactly. Label the field so
clients know which calendar it uses:

```python
>>> import json
>>> payload = json.dumps({"date_bs": date(2083, 6, 15).isoformat()})
>>> date.fromisoformat(json.loads(payload)["date_bs"])
sambat.date(2083, 6, 15)

```

With Pydantic, accept a `str` and validate it with `sambat.date.fromisoformat`
in a field validator; with pandas, convert columns of Gregorian dates using
`sambat.date.from_gregorian` (or ordinals) row by row.

## Pickle

`sambat.date` and `sambat.datetime` pickle by value, with a format that is
stable across sambat versions.
