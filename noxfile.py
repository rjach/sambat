"""Development sessions: ``uv run nox`` runs the same checks as CI."""

from __future__ import annotations

import nox

nox.needs_version = ">=2024.10.9"
nox.options.default_venv_backend = "uv"
nox.options.sessions = ["lint", "typecheck", "tests", "docs"]

PYTHONS = ["3.11", "3.12", "3.13", "3.14", "3.15"]


def _sync(session: nox.Session, *groups: str) -> None:
    args = [f"--group={group}" for group in groups]
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--no-default-groups",
        *args,
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )


@nox.session(python="3.14")
def lint(session: nox.Session) -> None:
    """Run ruff, the import-layer contracts and the calendar data check."""
    _sync(session, "lint")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")
    session.run("lint-imports")
    session.run("python", "tools/build_table.py", "--check")


@nox.session(python="3.14")
def typecheck(session: nox.Session) -> None:
    """Run mypy and pyright in strict mode and check public type completeness."""
    _sync(session, "typing")
    session.run("mypy")
    session.run("pyright")
    session.run("pyright", "--verifytypes", "sambat", "--ignoreexternal")


@nox.session(python=PYTHONS)
def tests(session: nox.Session) -> None:
    """Run the test suite with coverage."""
    _sync(session, "test")
    session.run("pytest", "--cov", "--cov-report=term-missing", *session.posargs)


@nox.session(python="3.14")
def doctests(session: nox.Session) -> None:
    """Run the examples in docstrings and the README."""
    _sync(session, "test")
    session.run(
        "pytest", "--doctest-modules", "src/sambat", "--doctest-glob=README.md", "README.md"
    )


@nox.session(python="3.14")
def docs(session: nox.Session) -> None:
    """Build the documentation with warnings as errors and run its examples."""
    _sync(session, "docs")
    session.run("pytest", "docs")
    session.run("sphinx-build", "-W", "--keep-going", "-b", "html", "docs", "docs/_build/html")


@nox.session(python="3.14")
def bench(session: nox.Session) -> None:
    """Run the performance benchmarks."""
    _sync(session, "bench")
    session.run("pytest", "benchmarks", "--benchmark-only", *session.posargs)


@nox.session(python="3.14")
def build(session: nox.Session) -> None:
    """Build the sdist and wheel into dist/ and check them."""
    session.run("uv", "build", external=True)
    session.run("uvx", "twine", "check", "--strict", "dist/*", external=True)
