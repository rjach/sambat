# The calendar data

sambat converts between calendars with a table of BS month lengths stored in
[`data/calendar.csv`](https://github.com/rjach/sambat/blob/main/data/calendar.csv).
The table is the only data in the package, and it is generated into
`sambat/_table.py` by `tools/build_table.py`, which also validates it.

## What is in the table

- One row per BS year from 1975 to the last year with a published calendar
  (currently 2083).
- For each year: the Gregorian date of Baisakh 1 and the 12 month lengths.
  Storing both means a single wrong digit cannot silently shift every later
  date; the build fails instead.
- An **evidence level** and the sources for every row.

## Evidence levels

`verified`
: Checked month by month against a published panchang, citing the document
  and its checksum. BS 2082 and 2083 are verified against the national
  panchang of the Nepal Panchanga Nirnayak Bikas Samiti; BS 2081 against the
  Surya Panchanga.

`consensus`
: At least five independent open-source tables cover the year and at most one
  disagrees.

`disputed`
: The open-source tables disagree. Five years (1989, 1991, 1993, 2004 and 2062)
  are in this state. Each one, with the competing values and the reason for
  the chosen value, is documented in
  [`data/README.md`](https://github.com/rjach/sambat/blob/main/data/README.md).

Open-source tables often copy each other, so agreement between them is weaker
evidence than it seems: when the official BS 2083 calendar was published, 12
of 20 tables still carried an outdated projection for that year. Verifying
more rows against printed panchangs is the most valuable contribution to the
project; see {doc}`../how-to/calendar-data`.

## When a new year is published

The committee publishes each year's calendar in advance. A sambat release then
adds one row. Because a calendar change changes conversion results, it is
always a **minor** release; patch releases never change a result. Check the
range of the installed version with `sambat range`, `sambat.MAXYEAR` or
`sambat.calendar.supported_range()`, and upgrade at least once a year.
