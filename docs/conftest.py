"""Run every Python example in the documentation with Sybil."""

from __future__ import annotations

from doctest import ELLIPSIS, NORMALIZE_WHITESPACE

from sybil import Sybil
from sybil.parsers.myst import PythonCodeBlockParser, SkipParser

pytest_collect_file = Sybil(
    parsers=[
        PythonCodeBlockParser(doctest_optionflags=ELLIPSIS | NORMALIZE_WHITESPACE),
        SkipParser(),
    ],
    patterns=["*.md"],
).pytest()
