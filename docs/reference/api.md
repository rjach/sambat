# API reference

## `sambat`

```{eval-rst}
.. autoclass:: sambat.date
   :members:
   :special-members: __add__, __sub__

.. autoclass:: sambat.datetime
   :members:

.. autoclass:: sambat.NepalTimeZone
   :members: utcoffset, dst, tzname, fromutc

.. autofunction:: sambat.today_np

.. autofunction:: sambat.now_np

.. autodata:: sambat.MINYEAR
   :annotation: = first BS year in the calendar table

.. autodata:: sambat.MAXYEAR
   :annotation: = last BS year in the calendar table

.. class:: sambat.IsoCalendarDate

   The named tuple ``(year, week, weekday)`` returned by
   :meth:`sambat.date.isocalendar` (the standard library's own type).

.. data:: sambat.NEPAL_TZ

   The ``Asia/Kathmandu`` time zone; see :class:`sambat.NepalTimeZone`.

.. data:: sambat.timedelta
          sambat.time
          sambat.timezone
          sambat.tzinfo
          sambat.UTC

   The standard library's own objects (``sambat.timedelta is datetime.timedelta``).
```

## `sambat.calendar`

```{eval-rst}
.. automodule:: sambat.calendar
   :members:
   :exclude-members: c
```

## `sambat.delta`

```{eval-rst}
.. automodule:: sambat.delta
   :members:
```

## `sambat.periods`

```{eval-rst}
.. automodule:: sambat.periods
   :members:
```

## `sambat.fiscal`

```{eval-rst}
.. automodule:: sambat.fiscal
   :members:
```

## `sambat.locale`

```{eval-rst}
.. automodule:: sambat.locale
   :members:
```

## `sambat.text`

```{eval-rst}
.. automodule:: sambat.text
   :members:
```

## `sambat.compat`

```{eval-rst}
.. automodule:: sambat.compat
   :members:
```
