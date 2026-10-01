# How the Bikram Sambat calendar works

Bikram Sambat (विक्रम संवत्, also Vikram Samvat) is the official calendar of
Nepal. It is a **sidereal solar** calendar: each month begins when the Sun
enters the next sidereal zodiac sign (its *sankranti*), and the year begins
with Baishakh in mid-April.

| # | Month | नेपाली | Begins around |
|---|---|---|---|
| 1 | Baishakh | बैशाख | mid-April |
| 2 | Jestha | जेठ | mid-May |
| 3 | Asar | असार | mid-June |
| 4 | Shrawan | साउन | mid-July |
| 5 | Bhadra | भदौ | mid-August |
| 6 | Ashwin (Asoj) | असोज | mid-September |
| 7 | Kartik | कात्तिक | mid-October |
| 8 | Mangsir | मंसिर | mid-November |
| 9 | Poush | पुस | mid-December |
| 10 | Magh | माघ | mid-January |
| 11 | Falgun | फागुन | mid-February |
| 12 | Chaitra | चैत | mid-March |

Because the Sun's apparent speed varies through the year, months have 29 to
32 days: the summer months (Jestha to Shrawan) are long, and the winter months
(Poush to Falgun) are short. The year has 365 or 366 days, but there is **no
leap-year rule**; the length follows from the month lengths.

The BS year is 56 or 57 years ahead of the Gregorian year: BS 2083 runs from
14 April 2026 to 13 April 2027.

## Who decides the month lengths

Each year's calendar is decided and published in advance by the
[Nepal Panchanga Nirnayak Bikas Samiti](https://npns.gov.np) (Nepal Calendar
Determination Development Committee), a body of the Government of Nepal. The
committee's decision is what makes a date legally and socially correct, so a
formula cannot replace it. See {doc}`calendar-data` and {doc}`scope`.

## Day numbers and weekdays

A BS day is the same civil day as its Gregorian equivalent, so weekdays
are the same and `sambat.date.toordinal()` returns the standard library's
proleptic Gregorian ordinal. Nepali calendars traditionally start the week on
Sunday (आइतबार); `sambat.calendar` defaults to Monday like the standard
library, and accepts `firstweekday=SUNDAY`.
