"""Performance benchmarks; run with ``uv run nox -s bench``.

Each benchmark is paired with its standard-library equivalent so regressions
show up as a ratio rather than an absolute time.
"""

from __future__ import annotations

import datetime as dt

from pytest_benchmark.fixture import BenchmarkFixture

import sambat

ORDINAL = sambat.date(2083, 6, 15).toordinal()


def test_stdlib_fromordinal(benchmark: BenchmarkFixture) -> None:
    benchmark(dt.date.fromordinal, ORDINAL)


def test_bs_fromordinal(benchmark: BenchmarkFixture) -> None:
    benchmark(sambat.date.fromordinal, ORDINAL)


def test_bs_constructor(benchmark: BenchmarkFixture) -> None:
    benchmark(sambat.date, 2083, 6, 15)


def test_bs_to_gregorian(benchmark: BenchmarkFixture) -> None:
    benchmark(sambat.date(2083, 6, 15).to_gregorian)


def test_stdlib_strftime(benchmark: BenchmarkFixture) -> None:
    benchmark(dt.date(2026, 10, 1).strftime, "%A, %d %B %Y")


def test_bs_strftime(benchmark: BenchmarkFixture) -> None:
    benchmark(sambat.date(2083, 6, 15).strftime, "%A, %d %B %Y")


def test_bs_strptime(benchmark: BenchmarkFixture) -> None:
    benchmark(sambat.date.strptime, "15 Ashwin 2083", "%d %B %Y")


def test_bs_datetime_astimezone(benchmark: BenchmarkFixture) -> None:
    value = sambat.datetime(2083, 6, 15, 9, 30, tzinfo=sambat.NEPAL_TZ)
    benchmark(value.astimezone, dt.UTC)
