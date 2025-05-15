"""Sphinx helper functions."""

from __future__ import annotations

import contextlib
import importlib.util
import logging
import os
import pathlib
import re
import sys
import tempfile
import typing as t

from . import _docutils, _extras

if _extras.SPHINX_INSTALLED:
    import sphinx.application
    import sphinx.domains.c
    import sphinx.domains.cpp
    import sphinx.domains.javascript
    import sphinx.domains.python
    import sphinx.domains.std
    import sphinx.util.docutils


logger = logging.getLogger(__name__)


def create_dummy_sphinx_app(confdir: str | None = None) -> sphinx.application.Sphinx:
    """Create a dummy sphinx instance with temp dirs.
    
    :param confdir: Path to the directory containing conf.py file
    :return: Sphinx application instance
    """
    logger.debug("Create dummy sphinx application.")
    with tempfile.TemporaryDirectory() as temp_dir:
        outdir = pathlib.Path(temp_dir) / "_build"
        return sphinx.application.Sphinx(
            srcdir=temp_dir,
            confdir=confdir,
            outdir=str(outdir),
            doctreedir=str(outdir),
            buildername="dummy",
            # NOTE: https://github.com/sphinx-doc/sphinx/issues/10483
            status=None,
        )


def find_conf_py(source_file: pathlib.Path | None) -> str | None:
    """Find the Sphinx conf.py file by traversing up from the source file.
    
    :param source_file: Path to the source file being checked
    :return: Path to the conf.py file or None if not found
    """
    if source_file is None:
        return None
    
    # Start from the directory of the source file
    current_dir = source_file.parent
    
    # Traverse up to find conf.py
    while current_dir != current_dir.parent:  # Stop at root
        conf_py_path = current_dir / "conf.py"
        if conf_py_path.exists():
            logger.debug("Found conf.py at %s", conf_py_path)
            return str(conf_py_path.parent)
        
        # Check for docs/source/conf.py pattern
        docs_source_conf = current_dir / "docs" / "source" / "conf.py"
        if docs_source_conf.exists():
            logger.debug("Found conf.py at %s", docs_source_conf)
            return str(docs_source_conf.parent)
        
        # Move up one directory
        current_dir = current_dir.parent
    
    return None


def extract_from_conf_py(conf_dir: str) -> tuple[list[str], list[str], list[str]]:
    """Extract custom directives, roles, and substitutions from conf.py.
    
    :param conf_dir: Directory containing conf.py
    :return: Tuple of (directives, roles, substitutions)
    """
    conf_path = os.path.join(conf_dir, "conf.py")
    if not os.path.exists(conf_path):
        return [], [], []
    
    # Load the conf.py module
    spec = importlib.util.spec_from_file_location("conf", conf_path)
    if spec is None or spec.loader is None:
        return [], [], []
    
    conf = importlib.util.module_from_spec(spec)
    
    # Add the conf.py directory to sys.path temporarily
    original_path = sys.path.copy()
    sys.path.insert(0, conf_dir)
    
    try:
        # Execute the conf.py file
        spec.loader.exec_module(conf)
        
        # Extract directives, roles, and substitutions
        directives = []
        roles = []
        substitutions = []
        
        # Check for extensions that might define directives and roles
        extensions = getattr(conf, "extensions", [])
        
        # Check for extlinks (common in Sphinx conf.py)
        extlinks = getattr(conf, "extlinks", {})
        if extlinks:
            # Each key in extlinks becomes a role
            roles.extend(extlinks.keys())
        
        # Check for rst_epilog and rst_prolog for substitutions
        for attr in ["rst_epilog", "rst_prolog"]:
            text = getattr(conf, attr, "")
            if text:
                # Look for substitution definitions like |name|
                subs = re.findall(r"\.\. \|([^|]+)\|", text)
                substitutions.extend(subs)
        
        return directives, roles, substitutions
    
    except Exception as e:
        logger.warning("Error loading conf.py: %s", e)
        return [], [], []
    
    finally:
        # Restore the original sys.path
        sys.path = original_path


@contextlib.contextmanager
def load_sphinx_if_available(source_file: pathlib.Path | None = None) -> t.Generator[sphinx.application.Sphinx | None, None, None]:
    """Contextmanager to register Sphinx directives and roles if sphinx is available.
    
    :param source_file: Path to the source file being checked
    :yield: None
    """
    if _extras.SPHINX_INSTALLED:
        # Find conf.py if source_file is provided
        conf_dir = find_conf_py(source_file)
        
        # Create dummy Sphinx app with conf_dir if found
        create_dummy_sphinx_app(conf_dir)
        
        # NOTE: Hack to prevent sphinx warnings for overwriting registered nodes; see #113
        sphinx.application.builtin_extensions = [
            e
            for e in sphinx.application.builtin_extensions
            if e != "sphinx.addnodes"  # type: ignore[assignment]
        ]
        
        # If conf.py was found, extract and register custom directives, roles, and substitutions
        if conf_dir:
            custom_directives, custom_roles, custom_substitutions = extract_from_conf_py(conf_dir)
            if custom_directives or custom_roles:
                logger.debug(
                    "Registering custom directives and roles from conf.py: %s directives, %s roles",
                    len(custom_directives), len(custom_roles)
                )
                _docutils.ignore_directives_and_roles(custom_directives, custom_roles)

    yield None


def get_sphinx_directives_and_roles() -> tuple[list[str], list[str]]:
    """Return Sphinx directives and roles loaded from sphinx.

    :return: Tuple of directives and roles
    """
    _extras.install_guard("sphinx")

    sphinx_directives = list(sphinx.domains.std.StandardDomain.directives)
    sphinx_roles = list(sphinx.domains.std.StandardDomain.roles)

    for domain in [
        sphinx.domains.c.CDomain,
        sphinx.domains.cpp.CPPDomain,
        sphinx.domains.javascript.JavaScriptDomain,
        sphinx.domains.python.PythonDomain,
    ]:
        domain_directives = list(domain.directives)
        domain_roles = list(domain.roles)

        sphinx_directives += domain_directives + [
            f"{domain.name}:{item}" for item in domain_directives
        ]

        sphinx_roles += domain_roles + [f"{domain.name}:{item}" for item in domain_roles]

    sphinx_directives += list(
        sphinx.util.docutils.directives._directives  # type: ignore[attr-defined]  # noqa: SLF001
    )
    sphinx_roles += list(
        sphinx.util.docutils.roles._roles  # type: ignore[attr-defined]  # noqa: SLF001
    )

    return (sphinx_directives, sphinx_roles)


_DIRECTIVE_WHITELIST = ["code", "code-block", "sourcecode", "include"]
_ROLE_WHITELIST: list[str] = []


def filter_whitelisted_directives_and_roles(
    directives: list[str], roles: list[str]
) -> tuple[list[str], list[str]]:
    """Filter whitelisted directives and roles out of input.

    :param directives: Directives to filter
    :param roles: Roles to filter
    :return: Tuple of filtered directives and roles
    """
    directives = list(filter(lambda d: d not in _DIRECTIVE_WHITELIST, directives))
    roles = list(filter(lambda r: r not in _ROLE_WHITELIST, roles))

    return (directives, roles)


def load_sphinx_ignores(source_file: pathlib.Path | None = None) -> None:  # pragma: no cover
    """Register Sphinx directives and roles to ignore.
    
    :param source_file: Path to the source file being checked
    """
    _extras.install_guard("sphinx")
    logger.debug("Load sphinx directives and roles.")

    (directives, roles) = get_sphinx_directives_and_roles()
    (directives, roles) = filter_whitelisted_directives_and_roles(directives, roles)

    # If source_file is provided, try to find conf.py and extract custom directives, roles, and substitutions
    if source_file is not None:
        conf_dir = find_conf_py(source_file)
        if conf_dir:
            custom_directives, custom_roles, custom_substitutions = extract_from_conf_py(conf_dir)
            directives.extend(custom_directives)
            roles.extend(custom_roles)
            # Substitutions are handled separately in checker.py

    _docutils.ignore_directives_and_roles(directives, roles)
