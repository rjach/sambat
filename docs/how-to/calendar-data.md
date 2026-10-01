# Verify or add a calendar year

The month-length table lives in `data/calendar.csv`. Verifying rows against a
published panchang is the most useful contribution you can make. The full
procedure, including the invariants enforced by `tools/build_table.py`, is in
[`data/README.md`](https://github.com/rjach/sambat/blob/main/data/README.md).

In short:

1. Get a published panchang for the year (the national panchang is published
   at <https://npns.gov.np>).
2. Read every month boundary (the day the day number returns to 1), the
   Gregorian date printed for it, and the weekday of Baisakh 1.
3. Update the row, set `evidence` to `verified`, and cite the document in
   `data/sources.toml` with its URL and SHA-256 checksum.
4. Run `uv run python tools/build_table.py` to regenerate the table.
5. Add a `calendar` news fragment in `changelog.d/` and open a pull request
   using the "New calendar year" or "Calendar discrepancy" template.

Changes to calendar data are released as a new minor version.
