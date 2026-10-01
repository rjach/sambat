"""Invariants of the generated calendar table and the integer lookups."""

from __future__ import annotations

import csv
import datetime as dt
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from sambat import _lookup, _table

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent


def test_month_and_year_lengths() -> None:
    for offset, lengths in enumerate(_table.MONTH_LENGTHS):
        year = _table.FIRST_YEAR + offset
        assert len(lengths) == 12, year
        assert all(29 <= length <= 32 for length in lengths), year
        assert sum(lengths) in {365, 366}, year


def test_year_starts_are_contiguous() -> None:
    starts = _table.YEAR_START_ORDINALS
    assert len(starts) == len(_table.MONTH_LENGTHS) + 1
    for index, lengths in enumerate(_table.MONTH_LENGTHS):
        assert starts[index + 1] - starts[index] == sum(lengths)


def test_new_year_falls_in_mid_april() -> None:
    for start in _table.YEAR_START_ORDINALS:
        new_year = dt.date.fromordinal(start)
        assert new_year.month == 4
        assert 12 <= new_year.day <= 15


def test_range_constants() -> None:
    assert _lookup.MINYEAR == _table.FIRST_YEAR
    assert _table.FIRST_YEAR + len(_table.MONTH_LENGTHS) - 1 == _lookup.MAXYEAR
    assert _lookup.ordinal_to_ymd(_lookup.MIN_ORDINAL) == (_lookup.MINYEAR, 1, 1)
    last = _lookup.ordinal_to_ymd(_lookup.MAX_ORDINAL)
    assert last == (_lookup.MAXYEAR, 12, _lookup.days_in_month(_lookup.MAXYEAR, 12))


def test_every_day_round_trips() -> None:
    for ordinal in range(_lookup.MIN_ORDINAL, _lookup.MAX_ORDINAL + 1):
        assert _lookup.ymd_to_ordinal(*_lookup.ordinal_to_ymd(ordinal)) == ordinal


def test_lookup_errors() -> None:
    with pytest.raises(ValueError, match="month must be"):
        _lookup.days_in_month(2083, 13)
    with pytest.raises(ValueError, match="out of range"):
        _lookup.days_in_year(_lookup.MAXYEAR + 1)
    with pytest.raises(ValueError, match="out of range"):
        _lookup.year_start_ordinal(_lookup.MAXYEAR + 2)
    assert _lookup.year_start_ordinal(_lookup.MAXYEAR + 1) == _table.YEAR_START_ORDINALS[-1]


def test_week_lookup_errors() -> None:
    with pytest.raises(ValueError, match="weekday"):
        _lookup.week_to_ordinal(2083, 1, 8)
    with pytest.raises(ValueError, match="week"):
        _lookup.week_to_ordinal(2083, 0, 1)
    with pytest.raises(ValueError, match="out of range"):
        _lookup.week_to_ordinal(_lookup.MAXYEAR + 2, 1, 1)
    with pytest.raises(ValueError, match="outside the supported range"):
        _lookup.week_to_ordinal(_lookup.MAXYEAR + 1, 2, 1)
    with pytest.raises(ValueError, match="outside the supported range"):
        _lookup.ordinal_to_week(_lookup.MIN_ORDINAL)


def test_csv_matches_generated_table() -> None:
    with (ROOT / "data" / "calendar.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert int(rows[0]["bs_year"]) == _table.FIRST_YEAR
    for offset, row in enumerate(rows):
        lengths = tuple(int(row[f"m{month:02d}"]) for month in range(1, 13))
        assert lengths == _table.MONTH_LENGTHS[offset]
        anchor = dt.date.fromisoformat(row["baisakh1_ad"]).toordinal()
        assert anchor == _table.YEAR_START_ORDINALS[offset]


def test_build_table_check_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_table.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _load_build_table() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_table", ROOT / "tools" / "build_table.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("build_table", module)
    spec.loader.exec_module(sys.modules["build_table"])
    return sys.modules["build_table"]


HEADER = "bs_year,baisakh1_ad," + ",".join(f"m{n:02d}" for n in range(1, 13))
HEADER += ",evidence,sources,notes\n"
GOOD_2082 = "2082,2025-04-14,31,31,32,31,31,31,30,29,30,29,30,30,verified,npns-panchang-2082,\n"
GOOD_2083 = "2083,2026-04-14,31,31,32,31,31,31,30,29,30,29,30,30,verified,npns-panchang-2083,\n"


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ("", "no rows"),
        (GOOD_2082.replace(",31,31,32,", ",31,31,33,", 1), "outside 29..32"),
        (GOOD_2082.replace(",30,30,verified", ",32,32,verified"), "not 365 or 366"),
        (GOOD_2082.replace("verified", "guessed"), "unknown evidence"),
        (GOOD_2082.replace("npns-panchang-2082", "nowhere"), "not defined"),
        (GOOD_2082.replace("2025-04-14", "2025-14-04"), "malformed"),
        (GOOD_2082 + GOOD_2083.replace("2026-04-14", "2026-04-15"), "Baisakh 1"),
        (GOOD_2082 + GOOD_2083.replace("2083,", "2084,", 1), "gap"),
    ],
)
def test_build_table_rejects_bad_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rows: str, message: str
) -> None:
    module = _load_build_table()
    csv_path = tmp_path / "calendar.csv"
    csv_path.write_text(HEADER + rows, encoding="utf-8")
    monkeypatch.setattr(module, "CSV_PATH", csv_path)
    with pytest.raises(module.CalendarDataError, match=message):
        module.load_rows()


def test_build_table_writes_and_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load_build_table()
    csv_path = tmp_path / "calendar.csv"
    csv_path.write_text(HEADER + GOOD_2082 + GOOD_2083, encoding="utf-8")
    table_path = tmp_path / "_table.py"
    monkeypatch.setattr(module, "CSV_PATH", csv_path)
    monkeypatch.setattr(module, "TABLE_PATH", table_path)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    assert module.main(["--check"]) == 1
    assert module.main([]) == 0
    assert module.main(["--check"]) == 0
    namespace: dict[str, object] = {}
    exec(table_path.read_text(encoding="utf-8"), namespace)  # noqa: S102
    assert namespace["FIRST_YEAR"] == 2082
    csv_path.write_text(HEADER, encoding="utf-8")
    assert module.main([]) == 1
    assert "no rows" in capsys.readouterr().err
