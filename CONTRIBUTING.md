# Contributing to sambat

Thank you for helping. sambat aims to be small and **exact**: every function is
either pure logic or backed by verified calendar data. Please keep that bar in
mind when proposing features. Anything that would need an approximate model, a
policy that changes over time, or data that must be refreshed regularly is out
of scope.

## Ways to contribute

- **Verify calendar rows.** Most rows in [`data/calendar.csv`](data/calendar.csv)
  are cross-checked against open-source tables but not yet against a printed
  panchang. Checking a year against a published panchang is the most valuable
  contribution you can make. See [Calendar data](#calendar-data).
- **Report bugs** with a minimal reproduction, using the bug report form.
- **Report a calendar discrepancy** if a conversion disagrees with a published
  Nepali calendar, using the calendar discrepancy form.
- **Improve the documentation** and examples.

## Development setup

sambat uses [uv](https://docs.astral.sh/uv/) for environments and
[nox](https://nox.thea.codes/) to run the same checks as CI.

```console
git clone https://github.com/rjach/sambat.git
cd sambat
uv sync                 # creates .venv with every development dependency
uv run pre-commit install
```

Common commands:

```console
uv run pytest                    # tests
uv run pytest --cov              # tests with coverage (95% minimum)
uv run ruff check . && uv run ruff format --check .
uv run mypy && uv run pyright    # strict type checking
uv run lint-imports              # architectural layering contracts
uv run nox                       # everything, on every installed Python
uv run nox -s docs               # build the documentation into docs/_build/html
```

## Pull requests

1. Open an issue first for anything larger than a small fix, so the approach
   can be agreed before you write code.
2. Create a branch from `main`. Keep each pull request focused on one change.
3. Add tests. Behaviour that mirrors the standard library should be checked
   against the standard library, ideally with a Hypothesis property.
4. Add a news fragment in [`changelog.d/`](changelog.d/) (see below), unless
   the change is invisible to users (the `skip-changelog` label skips the check).
5. Make sure `uv run nox` passes locally.
6. Sign off your commits (`git commit -s`) to certify the
   [Developer Certificate of Origin](https://developercertificate.org/).

All pull requests need a passing CI run (the `ci-pass` check) and an approving
review before they are squash-merged into `main`.

### News fragments

Changelog entries are assembled by [towncrier](https://towncrier.readthedocs.io/)
from files in `changelog.d/` named `<issue or PR number>.<type>.md`, for example
`changelog.d/42.feature.md`. The types are:

| Type | Use for |
|---|---|
| `calendar` | Any change to `data/calendar.csv` (new year, verification, correction) |
| `breaking` | Backwards-incompatible changes |
| `deprecation` | Newly deprecated APIs |
| `feature` | New features |
| `bugfix` | Bug fixes |
| `doc` | Documentation-only changes |
| `misc` | Internal changes that need no description |

Write one or two sentences in the past tense, for users.

## Calendar data

The table in [`data/calendar.csv`](data/calendar.csv) is the only data in
sambat. [`data/README.md`](data/README.md) explains its invariants and
evidence levels. To add or verify a year:

1. Obtain a published panchang for the year: the national panchang of the
   [Nepal Panchanga Nirnayak Bikas Samiti](https://npns.gov.np), or another
   published almanac.
2. Record every month boundary (the day the day number resets to 1), the
   Gregorian date printed for it, and the weekday of Baisakh 1.
3. Update the row, set `evidence` to `verified`, and add the source to
   [`data/sources.toml`](data/sources.toml) with a URL and a SHA-256 checksum.
4. Regenerate the table: `uv run python tools/build_table.py`.
5. Add a `calendar` news fragment.

Calendar changes are always released as a new **minor** version, because they
change conversion results. Patch releases never change a result.

## Coding guidelines

- Pure Python, no runtime dependencies, Python 3.11+.
- Fully typed: `mypy --strict` and `pyright` (strict) must pass, and public
  APIs keep a 100% `pyright --verifytypes` score.
- Public functions and classes have Google-style docstrings with examples that
  run as doctests.
- Mirror the standard library's names, signatures, error types and messages
  wherever sambat mirrors a stdlib API.
- Respect the layering in `pyproject.toml` (`[tool.importlinter]`): the
  calendar core never imports the public classes.

## Releasing (maintainers)

1. Make sure `main` is green and `changelog.d/` describes the release.
2. Run `uv run towncrier build --version X.Y.Z`, review `CHANGELOG.md`, and
   merge that change through a pull request.
3. Create and push a signed tag `vX.Y.Z` on `main`. The release workflow builds
   the distributions once, publishes to TestPyPI and then (after approval in
   the `pypi` environment) to PyPI using Trusted Publishing, attaches
   provenance attestations and creates the GitHub release.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By
participating you agree to uphold it.
