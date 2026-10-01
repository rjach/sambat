"""The public surface must track the running Python's ``datetime`` and ``calendar``.

When a new Python release adds a public name, these tests fail until sambat
implements it or documents the deviation in ``docs/reference/parity.md`` and
in the exclusion sets below.
"""

from __future__ import annotations

import calendar as stdlib_calendar
import datetime as dt
import inspect

import pytest

import sambat
from sambat import calendar as bs_calendar

# Dunders implemented by C slots that have no observable behaviour to mirror.
SLOT_ONLY = {
    "__class__",
    "__delattr__",
    "__dir__",
    "__doc__",
    "__getattribute__",
    "__getstate__",
    "__init__",
    "__init_subclass__",
    "__ne__",
    "__new__",
    "__reduce_ex__",
    "__rsub__",
    "__setattr__",
    "__sizeof__",
    "__subclasshook__",
}

MODULE_EXCLUSIONS = {"datetime_CAPI", "sys"}
CALENDAR_EXCLUSIONS = {
    # Gregorian month constants; sambat provides BAISHAKH..CHAITRA instead.
    "JANUARY",
    "FEBRUARY",
    "MARCH",
    "APRIL",
    "MAY",
    "JUNE",
    "JULY",
    "AUGUST",
    "SEPTEMBER",
    "OCTOBER",
    "NOVEMBER",
    "DECEMBER",
    # Switches the process C locale, which sambat never consults.
    "different_locale",
}


def _public(obj: object) -> set[str]:
    return {name for name in dir(obj) if not name.startswith("_") or name.endswith("__")}


@pytest.mark.parametrize(
    ("stdlib_cls", "sambat_cls"), [(dt.date, sambat.date), (dt.datetime, sambat.datetime)]
)
def test_class_surface(stdlib_cls: type, sambat_cls: type) -> None:
    missing = _public(stdlib_cls) - _public(sambat_cls) - SLOT_ONLY
    assert not missing, f"{sambat_cls.__name__} lacks {sorted(missing)}"


def test_module_surface() -> None:
    # __all__ is the documented API; dir() also lists implementation details
    # such as PyPy's cffi interop helpers.
    public = getattr(dt, "__all__", [name for name in dir(dt) if not name.startswith("_")])
    names = set(public) - MODULE_EXCLUSIONS
    missing = {name for name in names if not hasattr(sambat, name)}
    assert not missing, f"sambat lacks {sorted(missing)}"


def test_reexported_types_are_identical() -> None:
    assert sambat.timedelta is dt.timedelta
    assert sambat.time is dt.time
    assert sambat.timezone is dt.timezone
    assert sambat.tzinfo is dt.tzinfo
    assert sambat.UTC is dt.UTC


def test_calendar_module_surface() -> None:
    expected = set(stdlib_calendar.__all__) - CALENDAR_EXCLUSIONS
    missing = expected - set(bs_calendar.__all__)
    assert not missing, f"sambat.calendar lacks {sorted(missing)}"
    for name in ("format", "formatstring", "main", "prweek", "week"):
        assert hasattr(bs_calendar, name)


@pytest.mark.parametrize("name", ["Calendar", "TextCalendar", "HTMLCalendar"])
def test_calendar_class_surface(name: str) -> None:
    stdlib_cls = getattr(stdlib_calendar, name)
    sambat_cls = getattr(bs_calendar, name)
    stdlib_names = {n for n in dir(stdlib_cls) if not n.startswith("_")}
    sambat_names = {n for n in dir(sambat_cls) if not n.startswith("_")}
    missing = stdlib_names - sambat_names
    assert not missing, f"sambat.calendar.{name} lacks {sorted(missing)}"
    for method in stdlib_names:
        ours, theirs = getattr(sambat_cls, method), getattr(stdlib_cls, method)
        if not (inspect.isfunction(ours) and inspect.isfunction(theirs)):
            continue
        ours_params = list(inspect.signature(ours).parameters)
        theirs_params = [
            p.name
            for p in inspect.signature(theirs).parameters.values()
            if p.kind is not p.KEYWORD_ONLY
        ]
        assert ours_params[: len(theirs_params)] == theirs_params, f"{name}.{method}"


@pytest.mark.parametrize(
    "name",
    ["isleap", "leapdays", "weekday", "monthrange", "setfirstweekday", "timegm", "formatstring"],
)
def test_calendar_function_signatures(name: str) -> None:
    ours = inspect.signature(getattr(bs_calendar, name))
    theirs = inspect.signature(getattr(stdlib_calendar, name))
    assert list(ours.parameters) == list(theirs.parameters)
