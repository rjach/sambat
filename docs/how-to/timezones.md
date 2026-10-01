# Work with time zones in Nepal

`sambat.datetime` accepts any {class}`datetime.tzinfo`, including
{class}`zoneinfo.ZoneInfo`. Time-zone calls are made with the equivalent
standard-library datetime, so every tzinfo implementation behaves exactly as
it does with the standard library.

## `NEPAL_TZ`

`sambat.NEPAL_TZ` implements the IANA `Asia/Kathmandu` zone without needing
the `tzdata` package (useful on Windows and in slim containers):

| Period | UTC offset | `tzname()` |
|---|---|---|
| until 1920-01-01 | +05:41:16 (local mean time) | `LMT` |
| 1920-01-01 to 1986-01-01 | +05:30 | `+0530` |
| since 1986-01-01 | +05:45 | `+0545` |

```python
>>> import datetime
>>> from sambat import NEPAL_TZ
>>> datetime.datetime(1980, 1, 1, tzinfo=NEPAL_TZ).utcoffset()
datetime.timedelta(seconds=19800)
>>> datetime.datetime(2026, 1, 1, tzinfo=NEPAL_TZ).tzname()
'+0545'

```

The 1986 change skipped the wall times 00:00–00:14 on 1 January 1986, and the
1920 change repeated 11 minutes 16 seconds; `fold` follows PEP 495 for both.

## Current time in Nepal

```python
>>> import sambat
>>> sambat.now_np().utcoffset()
datetime.timedelta(seconds=20700)

```

`sambat.datetime.now()` without an argument returns naive machine-local time,
exactly like {meth}`datetime.datetime.now`.

## Converting between zones

```python
>>> from sambat import datetime as bs_datetime
>>> kathmandu = bs_datetime(2083, 6, 15, 9, 30, tzinfo=NEPAL_TZ)
>>> kathmandu.astimezone(sambat.UTC).isoformat()
'2083-06-15T03:45:00+00:00'

```
