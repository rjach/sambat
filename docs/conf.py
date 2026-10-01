"""Sphinx configuration for the sambat documentation."""

from __future__ import annotations

import urllib.error
import urllib.request

import sambat

PYTHON_DOCS = "https://docs.python.org/3"


def _reachable(url: str) -> bool:
    """Return whether an intersphinx inventory can be downloaded right now."""
    try:
        with urllib.request.urlopen(f"{url}/objects.inv", timeout=15) as response:  # noqa: S310
            return bool(response.status == 200)
    except (OSError, urllib.error.URLError):
        return False


project = "sambat"
author = "Rojan Acharya and the sambat contributors"
copyright = "2026, Rojan Acharya and the sambat contributors"  # noqa: A001
release = sambat.__version__
version = ".".join(release.split(".")[:2])

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinxext.opengraph",
]

source_suffix = {".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", "conftest.py"]

myst_enable_extensions = ["colon_fence", "deflist", "fieldlist"]
myst_heading_anchors = 3

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_typehints_format = "short"
autodoc_default_options = {"members": True, "show-inheritance": True}
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# Links to the Python documentation degrade to plain text (instead of failing
# the strict build) while docs.python.org is unreachable.
intersphinx_mapping = {"python": (PYTHON_DOCS, None)} if _reachable(PYTHON_DOCS) else {}

html_theme = "furo"
html_title = "sambat"
html_baseurl = "https://rjach.github.io/sambat/"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/rjach/sambat/",
    "source_branch": "main",
    "source_directory": "docs/",
}

ogp_site_url = html_baseurl
ogp_site_name = "sambat"
ogp_description_length = 200
ogp_social_cards = {"enable": False}

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True
