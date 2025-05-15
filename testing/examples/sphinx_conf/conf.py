"""Configuration file for the Sphinx documentation builder."""

from __future__ import annotations

import datetime
import typing as t

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx


project = "test_sphinx_conf"
author = "Test Author"
copyright = f"{datetime.datetime.now().year}, {author}"

# -- General configuration ---------------------------------------------------
extensions = []

# -- Options for extlinks extension ------------------------------------------
extensions.append("sphinx.ext.extlinks")
extlinks = {
    "issue": ("https://github.com/rstcheck/rstcheck-core/issues/%s", "#%s"),
    "pull": ("https://github.com/rstcheck/rstcheck-core/pull/%s", "PR#%s"),
    "user": ("https://github.com/%s", "@%s"),
}

# -- Custom substitutions ----------------------------------------------------
rst_prolog = """
.. |br| raw:: html

    <br/>
    
.. |project| replace:: test_sphinx_conf
"""

rst_epilog = """
.. |version| replace:: 1.0.0
"""

# -- Final setup -------------------------------------------------------------
def setup(app: Sphinx) -> None:
    """Connect custom func to sphinx events."""
    pass
