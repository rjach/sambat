from __future__ import annotations

import json
import subprocess
import sys

import pytest

from sambat import MAXYEAR, __version__, today_np
from sambat.__main__ import main


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    status = main(list(args))
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def test_today(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "today")
    assert status == 0
    assert today_np().isoformat() in out
    status, out, _ = run(capsys, "today", "--json", "--locale", "ne")
    payload = json.loads(out)
    assert payload["timezone"] == "Asia/Kathmandu"
    assert payload["text"].endswith(
        today_np().strftime("%Y", locale=__import__("sambat").locale.NE)
    )


def test_convert(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "convert", "2083-06-15")
    assert status == 0
    assert out.strip() == "2083-06-15 BS = 2026-10-01 AD (Thursday, 15 Ashwin 2083)"
    status, out, _ = run(capsys, "convert", "--to-bs", "2026-10-01", "--json")
    assert json.loads(out)["bs"] == "2083-06-15"


def test_convert_errors(capsys: pytest.CaptureFixture[str]) -> None:
    status, _, err = run(capsys, "convert", f"{MAXYEAR + 1}-01-01")
    assert status == 1
    assert "out of range" in err
    status, _, err = run(capsys, "convert", "--to-bs", "26-10-01")
    assert status == 1
    assert "error" in err


def test_cal(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "cal", "2083", "6", "--dual")
    assert status == 0
    assert "Ashwin 2083 (Sep–Oct 2026)" in out
    status, out, _ = run(capsys, "cal", "2083", "--first-weekday", "mon")
    assert status == 0
    assert "Mo Tu We" in out
    status, out, _ = run(capsys, "cal", "2083", "6", "--json")
    payload = json.loads(out)
    assert payload["months"][0]["days"] == 31
    assert payload["months"][0]["weeks"][0][0] is None
    status, out, _ = run(capsys, "cal")
    assert status == 0
    assert str(today_np().year) in out


def test_fy(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "fy", "2083-06-15", "--quarters", "--chaumasik", "--halves")
    assert status == 0
    assert "Fiscal year 2083/84" in out
    assert "quarter 4: beyond the supported calendar range" in out
    status, out, _ = run(capsys, "fy", "2082-06-15", "--quarters", "--json")
    payload = json.loads(out)
    assert payload["fiscal_year"] == "2082/83"
    assert payload["quarters"][3]["end"] == "2083-03-32"
    status, out, _ = run(capsys, "fy")
    assert status == 0


def test_invalid_locale_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["today", "--locale", "fr"])
    assert excinfo.value.code == 2
    assert "unknown locale" in capsys.readouterr().err


def test_diff_and_range(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "diff", "2056-04-12", "2083-06-15")
    assert status == 0
    assert out.startswith("27 years, 2 months, 3 days")
    status, out, _ = run(capsys, "range", "--json")
    assert json.loads(out)["max_year"] == MAXYEAR
    status, out, _ = run(capsys, "range")
    assert out.startswith("BS ")


def test_version_and_module_entry_point() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "sambat", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == f"sambat {__version__}"
