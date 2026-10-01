"""Packaging, public API and import-time structure."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from importlib import resources

import pytest

import sambat

PUBLIC_MODULES = ["calendar", "compat", "delta", "fiscal", "locale", "periods", "text"]
CORE_MODULES = {
    "sambat",
    "sambat._date",
    "sambat._datetime",
    "sambat._formatting",
    "sambat._isoformat",
    "sambat._lookup",
    "sambat._parsing",
    "sambat._table",
    "sambat._tz",
    "sambat._version",
    "sambat.locale",
    "sambat.text",
}


def test_all_names_exist() -> None:
    for name in sambat.__all__:
        assert hasattr(sambat, name), name
    for module_name in PUBLIC_MODULES:
        module = importlib.import_module(f"sambat.{module_name}")
        for name in module.__all__:
            assert hasattr(module, name), f"sambat.{module_name}.{name}"


def test_public_modules_are_lazy_attributes() -> None:
    assert sambat.fiscal.FiscalYear.__name__ == "FiscalYear"  # type: ignore[attr-defined]
    assert set(PUBLIC_MODULES) <= set(dir(sambat))
    with pytest.raises(AttributeError, match="no attribute"):
        _ = sambat.does_not_exist  # type: ignore[attr-defined]


def test_import_loads_only_the_core() -> None:
    code = (
        "import json, sys, sambat; "
        "print(json.dumps(sorted(m for m in sys.modules if m.startswith('sambat'))))"
    )
    output = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout
    loaded = set(json.loads(output))
    assert loaded <= CORE_MODULES, sorted(loaded - CORE_MODULES)


def test_typed_marker_is_shipped() -> None:
    assert resources.files("sambat").joinpath("py.typed").is_file()


def test_version() -> None:
    assert isinstance(sambat.__version__, str)
    assert sambat.__version__
