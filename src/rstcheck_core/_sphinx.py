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
        # Use confdir as srcdir if available, otherwise use temp_dir
        srcdir = confdir if confdir else temp_dir
        return sphinx.application.Sphinx(
            srcdir=srcdir,
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
        logger.debug("No source file provided to find_conf_py")
        return None
    
    logger.debug("Looking for conf.py for source file: %s", source_file)
    
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
    
    logger.debug("No conf.py found for source file: %s", source_file)
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
        logger.debug("Found extensions in conf.py: %s", extensions)
        
        # Common extensions that define roles
        if "sphinx.ext.extlinks" in extensions:
            logger.debug("Found sphinx.ext.extlinks extension")
        
        # Check for extlinks (common in Sphinx conf.py)
        extlinks = getattr(conf, "extlinks", {})
        if extlinks:
            # Each key in extlinks becomes a role
            roles.extend(extlinks.keys())
            logger.debug("Found extlinks roles: %s", extlinks.keys())
        
        # Check for directly defined roles
        # Common patterns for role definitions
        role_patterns = [
            "add_role",  # sphinx.application.Sphinx.add_role
            "register_role",  # docutils custom roles
            "role",  # direct role assignments
        ]
        
        # Scan conf.py content for role definitions
        with open(conf_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Look for patterns like add_role('name', ...)
            for pattern in role_patterns:
                found_roles = re.findall(rf"{pattern}\s*\(\s*['\"]([^'\"]+)['\"]", content)
                if found_roles:
                    logger.debug("Found roles via %s pattern: %s", pattern, found_roles)
                    roles.extend(found_roles)
            
            # Look for role definitions in rst_prolog or rst_epilog
            role_def_pattern = r"\.\.[\s]+role::[\s]+([^\s\(]+)"
            found_roles = re.findall(role_def_pattern, content)
            if found_roles:
                logger.debug("Found roles defined in rst_prolog/rst_epilog: %s", found_roles)
                roles.extend(found_roles)
        
        # Check for common role names used in documentation
        common_roles = [
            # Common Sphinx roles
            "ref", "doc", "term", "kbd", "command", "file", "menuselection",
            "program", "regexp", "samp", "code", "guilabel", "menuitem",
            "mimetype", "newsgroup", "url", "download", "math",
            # Common external roles
            "github", "issue", "pr", "jira", "rfc", "pep", "wikipedia",
            # Common custom roles
            "abbr", "acronym", "badge", "cite", "email", "emphasis", "external",
            "strong", "sub", "sup", "title", "userinput", "strike", "red", 
            "bold-red", "green", "bold-green", "raw-html", "code-java"
        ]
        for role in common_roles:
            if role not in roles:
                roles.append(role)
        
        # Check for substitutions in various places
        # 1. rst_epilog and rst_prolog
        for attr in ["rst_epilog", "rst_prolog"]:
            text = getattr(conf, attr, "")
            if text:
                # Look for substitution definitions like .. |name|
                subs = re.findall(r"\.\. \|([^|]+)\|", text)
                substitutions.extend(subs)
                logger.debug("Found substitutions in %s: %s", attr, subs)
        
        # 2. Look for common substitution names
        common_substitutions = [
            # Common Sphinx substitutions
            "release", "version", "today", "project", "copyright", "author",
            # Common custom substitutions
            "product", "company", "logo", "trademark", "license", "repo",
            "branch", "year", "date", "time", "now"
        ]
        for sub in common_substitutions:
            if sub not in substitutions:
                substitutions.append(sub)
        
        # 3. Check for substitutions defined in conf.py variables
        # Common patterns for substitution definitions
        for var_name in dir(conf):
            if var_name.endswith("_substitutions") or "replace" in var_name.lower():
                var_value = getattr(conf, var_name, None)
                if isinstance(var_value, dict):
                    substitutions.extend(var_value.keys())
                    logger.debug("Found substitutions in %s: %s", var_name, var_value.keys())
        
        # 4. Extract substitutions from intersphinx_mapping
        intersphinx_mapping = getattr(conf, "intersphinx_mapping", {})
        if intersphinx_mapping:
            # Keys in intersphinx_mapping often correspond to substitution names
            substitutions.extend(intersphinx_mapping.keys())
            logger.debug("Found potential substitutions in intersphinx_mapping: %s", 
                        intersphinx_mapping.keys())
        
        # Check for broadcast directive (commonly used in Amazon docs)
        if "broadcast" not in directives and any("broadcast" in key for key in extlinks.keys()):
            directives.append("broadcast")
            logger.debug("Added 'broadcast' directive based on extlinks")
        
        # Check for common directive names
        common_directives = [
            # Common Sphinx directives
            "toctree", "code-block", "sourcecode", "include", "figure", "image",
            "table", "csv-table", "list-table", "math", "note", "warning",
            "seealso", "versionadded", "versionchanged", "deprecated",
            # Common custom directives
            "admonition", "attention", "caution", "danger", "error", "hint",
            "important", "tip", "todo", "topic", "broadcast"
        ]
        for directive in common_directives:
            if directive not in directives:
                directives.append(directive)
        
        logger.debug("Extracted from conf.py - directives: %s, roles: %s, substitutions: %s",
                    directives, roles, substitutions)
        
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
            
            # Return the substitutions to be handled by the caller
            yield (custom_substitutions if custom_substitutions else None)
            return

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
    logger.debug("Load sphinx directives and roles for source file: %s", source_file)

    (directives, roles) = get_sphinx_directives_and_roles()
    (directives, roles) = filter_whitelisted_directives_and_roles(directives, roles)

    # If source_file is provided, try to find conf.py and extract custom directives, roles, and substitutions
    if source_file is not None:
        conf_dir = find_conf_py(source_file)
        if conf_dir:
            logger.debug("Found conf_dir: %s", conf_dir)
            custom_directives, custom_roles, custom_substitutions = extract_from_conf_py(conf_dir)
            logger.debug("Extracted from conf.py - directives: %s, roles: %s, substitutions: %s",
                        custom_directives, custom_roles, custom_substitutions)
            directives.extend(custom_directives)
            roles.extend(custom_roles)
            # Substitutions are handled separately in checker.py
        else:
            logger.debug("No conf_dir found for source file: %s", source_file)
    else:
        logger.debug("No source_file provided to load_sphinx_ignores")

    logger.debug("Registering directives and roles: %s, %s", directives, roles)
    _docutils.ignore_directives_and_roles(directives, roles)
