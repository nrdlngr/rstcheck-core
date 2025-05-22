"""Sphinx helper functions."""

from __future__ import annotations

import contextlib
import logging
import pathlib
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


def find_sphinx_confdir(source_file_dir: pathlib.Path) -> pathlib.Path | None:
    """Find directory containing conf.py file by traversing up the directory tree.
    
    :param source_file_dir: Directory to start searching from
    :return: Path to directory containing conf.py or None if not found
    """
    current_dir = source_file_dir
    while current_dir != current_dir.parent:  # Stop at filesystem root
        conf_path = current_dir / "conf.py"
        if conf_path.exists():
            logger.debug("Found conf.py at %s", conf_path)
            return current_dir
        current_dir = current_dir.parent
    
    return None


def create_dummy_sphinx_app(confdir: pathlib.Path | None = None) -> sphinx.application.Sphinx:
    """Create a dummy sphinx instance with temp dirs.
    
    :param confdir: Path to directory containing conf.py file; defaults to :py:obj:`None`
    :return: Sphinx application instance
    """
    logger.debug("Create dummy sphinx application.")
    with tempfile.TemporaryDirectory() as temp_dir:
        outdir = pathlib.Path(temp_dir) / "_build"
        return sphinx.application.Sphinx(
            srcdir=str(confdir) if confdir is not None else temp_dir,
            confdir=confdir,
            outdir=str(outdir),
            doctreedir=str(outdir),
            buildername="dummy",
            # NOTE: https://github.com/sphinx-doc/sphinx/issues/10483
            status=None,
        )


@contextlib.contextmanager
def load_sphinx_if_available(
    source_file_dir: pathlib.Path | None = None
) -> t.Generator[sphinx.application.Sphinx | None, None, None]:
    """Contextmanager to register Sphinx directives and roles if sphinx is available.
    
    :param source_file_dir: Directory of the source file being checked; defaults to :py:obj:`None`
    :yield: Sphinx application or None if Sphinx is not installed
    """
    app = None
    if _extras.SPHINX_INSTALLED:
        confdir = None
        if source_file_dir is not None:
            confdir = find_sphinx_confdir(source_file_dir)
        
        app = create_dummy_sphinx_app(confdir)
        
        # NOTE: Hack to prevent sphinx warnings for overwriting registered nodes; see #113
        sphinx.application.builtin_extensions = [
            e
            for e in sphinx.application.builtin_extensions
            if e != "sphinx.addnodes"  # type: ignore[assignment]
        ]

    yield app


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


def load_sphinx_ignores(app: sphinx.application.Sphinx | None = None) -> None:  # pragma: no cover
    """Register Sphinx directives and roles to ignore.
    
    :param app: Sphinx application instance; defaults to :py:obj:`None`
    """
    _extras.install_guard("sphinx")
    logger.debug("Load sphinx directives and roles.")

    (directives, roles) = get_sphinx_directives_and_roles()
    (directives, roles) = filter_whitelisted_directives_and_roles(directives, roles)

    _docutils.ignore_directives_and_roles(directives, roles)
