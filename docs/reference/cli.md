# Command line

Installing sambat provides the `sambat` command (also available as
`python -m sambat`). Every subcommand accepts `--json` and `--locale {en,ne}`.
Unlike the library, the CLI uses Nepal time and Sunday-first weeks by default.

| Command | Purpose |
|---|---|
| `sambat today` | Today's date in Nepal, in BS and AD |
| `sambat convert 2083-06-15` | BS → AD |
| `sambat convert --to-bs 2026-10-01` | AD → BS |
| `sambat cal [YEAR [MONTH]] [--dual] [--first-weekday mon]` | Print a month or year |
| `sambat fy [DATE] [--quarters] [--chaumasik] [--halves]` | Fiscal year of a BS date |
| `sambat diff START END` | Years, months and days between two BS dates |
| `sambat range` | The BS range supported by the installed version |

```console
$ sambat convert 2083-06-15
2083-06-15 BS = 2026-10-01 AD (Thursday, 15 Ashwin 2083)
$ sambat fy 2082-10-05 --quarters
Fiscal year 2082/83 (starts 2082-04-01 BS)
2082-10-05 BS is in month 7, quarter 3, chaumasik 2, half 2
  quarter 1: 2082-04-01 .. 2082-06-31 (93 days)
  quarter 2: 2082-07-01 .. 2082-09-30 (89 days)
  quarter 3: 2082-10-01 .. 2082-12-30 (89 days)
  quarter 4: 2083-01-01 .. 2083-03-32 (94 days)
```

`python -m sambat.calendar` mirrors `python -m calendar`
(`[-t text|html] [-L en|ne] [-f FIRST_WEEKDAY] [--dual] [year [month]]`).
