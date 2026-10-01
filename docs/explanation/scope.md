# Why sambat is exact or nothing

sambat follows one rule: **a feature ships only if its output is exactly right
by construction**. Arithmetic, formatting and parsing are pure logic, checked
against the standard library by tests. Fixed definitions, such as Nepal's
fiscal year starting on Shrawan 1 or the Devanagari digit code points, never
change.

## The one exception: the calendar table

BS month lengths cannot be computed exactly. They are decided by a committee,
which bases them on astronomical calculation but publishes the result as a
decision. An astronomical prototype written while planning sambat reproduced
about 95% of historical month starts, which means roughly one wrong month
every two years. That is not good enough for dates on documents.

So sambat ships a table of published years and **refuses to guess** beyond
it. A date in an unpublished year raises `ValueError` with an explanation,
instead of silently returning a projection that might later prove wrong.

## What sambat deliberately does not do

| Not included | Why |
|---|---|
| Projected future years | Only the committee decides them; a projection can be wrong. |
| Astronomical computation (sankranti, sunrise, tithi, panchang) | Model-based, with error margins and no single agreed reference. |
| Festivals and public holidays | Decided by committees and the government each year, and amended at short notice. |
| Business days and weekends | Policy that changes (Nepal briefly had a two-day weekend in 2022) and needs holiday data. |
| Natural-language dates ("३ दिन अघि"), number words | Conventions and spellings vary; there is no single correct output. |
| Free-text date guessing | Ambiguous input would be guessed. `strptime` with an explicit format is exact. |
| Framework integrations | They need constant upkeep; storing `to_gregorian()` and `isoformat()` values is exact and works everywhere ({doc}`../how-to/storage`). |

These limits keep sambat small, predictable and maintainable: the only
recurring work is adding one row to the calendar table each year.
