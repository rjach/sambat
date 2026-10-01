# Calendar data

Bikram Sambat month lengths are not produced by a formula. Each year's
calendar is decided and published by the Nepal Panchanga Nirnayak Bikas
Samiti (Government of Nepal). `sambat` therefore ships a table of published
years and refuses to guess outside it.

| File | Purpose |
|---|---|
| [`calendar.csv`](calendar.csv) | One row per BS year: Baisakh 1 in the Gregorian calendar, the 12 month lengths, the evidence level, the source ids and notes. The single source of truth. |
| [`sources.toml`](sources.toml) | Every source referenced from `calendar.csv` (`[[source]]`), and the open-source tables used for cross-checking (`[[dataset]]`), with URLs, commits, checksums and licences. |

`src/sambat/_table.py` is generated from `calendar.csv` by
`python tools/build_table.py` and must never be edited by hand. CI runs
`python tools/build_table.py --check` on every change.

## Invariants (checked by `tools/build_table.py`)

- Every month has 29 to 32 days; every year has 365 or 366 days.
- Years are contiguous, and `baisakh1_ad` of each year equals the previous
  year's `baisakh1_ad` plus that year's length. Storing both the anchor and the
  lengths means a single typo cannot silently shift every later date.
- Every row has a known evidence level and only references ids defined in
  `sources.toml`.

## Evidence levels

| Level | Meaning | Rows |
|---|---|---|
| `verified` | Checked month by month against a published panchang: every month boundary (where the day number resets to 1), the printed Gregorian dates and the weekday of Baisakh 1. The source is cited in `sources.toml`. | 2081 (Surya Panchanga), 2082 and 2083 (the Samiti's national panchang) |
| `consensus` | At least five independent open-source tables cover the year and at most one disagrees. | 101 rows |
| `disputed` | Open-source tables disagree. The chosen value and the evidence are listed below. | 1989, 1991, 1993, 2004, 2062 |

Many open-source tables are copies of each other, so the number of tables
agreeing is weaker evidence than it looks. For example, 12 of the 20 tables
that cover BS 2083 still carry an outdated projection that the official
panchang contradicts. Only `verified` rows have been checked against a
primary source.

## Disputed rows

### BS 1989

| Month lengths | Tables | Chosen |
|---|---|---|
| 31 31 31 32 31 31 29 30 30 29 30 30 | 6 | yes |
| 31 31 31 32 31 31 30 29 30 29 30 30 | 4 |  |

The variants differ only in where Kartik ends.

### BS 1991

| Month lengths | Tables | Chosen |
|---|---|---|
| 31 32 31 32 31 30 30 30 29 29 30 30 | 7 | yes |
| 31 32 31 32 31 30 30 29 30 29 30 30 | 3 |  |

### BS 1993

| Month lengths | Tables | Chosen |
|---|---|---|
| 31 31 32 31 31 31 30 29 30 29 30 30 | 6 | yes |
| 31 31 31 32 31 31 30 29 30 29 30 30 | 3 |  |

### BS 2004

| Month lengths | Tables | Chosen |
|---|---|---|
| 30 32 31 32 31 30 30 30 29 30 29 31 | 16 | yes |
| 30 32 31 32 31 30 30 30 30 29 29 31 | 4 |  |

### BS 2062

| Month lengths | Tables | Chosen |
|---|---|---|
| 30 32 31 32 31 31 29 30 29 30 29 31 | 14 |  |
| 31 31 31 32 31 31 29 30 29 30 29 31 | 7 | yes |

nepali-datetime deliberately changed this row to the chosen value in
September 2024 ("fix date for year 2062"). The majority value is the older
one shared by many copied tables. The variants differ only in whether Jestha 1
fell on 14 or 15 May 2005; the Vrishabha sankranti that year fell close to
local midnight, so astronomy cannot settle it.

### Resolved: BS 2081

Open-source tables disagreed about 2081 (12 of 20 matched the chosen value).
The row is now `verified` against the Surya Panchanga for 2081: Baisakh 1 is
Saturday 13 April 2024, and every month boundary matches.

## Adding a year or verifying a row

1. Find the official panchang (or another primary government publication) for
   the year. The Samiti publishes it at <https://npns.gov.np>.
2. Read every month boundary and the weekday of Baisakh 1.
3. Add or update the row in `calendar.csv` with `evidence = verified`, and add
   the source to `sources.toml` with its URL and SHA-256 checksum.
4. Run `python tools/build_table.py` and commit the regenerated table.
5. Add a news fragment in `changelog.d/` of type `calendar`.

Any change to `calendar.csv` is released as a **minor** version. Patch
releases never change a conversion result.
