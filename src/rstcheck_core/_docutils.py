"""Docutils helper functions."""

from __future__ import annotations

import importlib
import logging
import typing as t

import docutils.nodes
import docutils.parsers.rst.directives
import docutils.parsers.rst.roles
import docutils.parsers.rst.states
import docutils.writers

from . import _extras

logger = logging.getLogger(__name__)


class IgnoredDirective(docutils.parsers.rst.Directive):  # pragma: no cover
    """Stub for unknown directives."""

    has_content = True

    def run(self) -> list:  # type: ignore[type-arg]
        """Do nothing."""
        return []


def ignore_role(  # noqa: PLR0913
    name: str,  # noqa: ARG001
    rawtext: str,  # noqa: ARG001
    text: str,  # noqa: ARG001
    lineno: int,  # noqa: ARG001
    inliner: docutils.parsers.rst.states.Inliner,  # noqa: ARG001
    options: t.Mapping[str, t.Any] | None = None,  # noqa: ARG001
    content: t.Sequence[str] | None = None,  # noqa: ARG001
) -> tuple[
    t.Sequence[docutils.nodes.reference], t.Sequence[docutils.nodes.reference]
]:  # pragma: no cover
    """Stub for unknown roles."""
    return ([], [])


def clean_docutils_directives_and_roles_cache() -> None:  # pragma: no cover
    """Clean docutils' directives and roles cache by reloading their modules.

    Reloads:
    - :py:mod:`docutils.parsers.rst.directives`
    - :py:mod:`docutils.parsers.rst.roles`
    """
    logger.info("Reload module docutils.parsers.rst.directives/roles")
    importlib.reload(docutils.parsers.rst.directives)
    importlib.reload(docutils.parsers.rst.roles)


def ignore_directives_and_roles(directives: list[str], roles: list[str]) -> None:
    """Ignore directives and roles in docutils.

    :param directives: Directives to ignore
    :param roles: Roles to ignore
    """
    for directive in directives:
        docutils.parsers.rst.directives.register_directive(directive, IgnoredDirective)

    for role in roles:
        docutils.parsers.rst.roles.register_local_role(role, ignore_role)


def register_substitutions_and_targets(substitutions: dict[str, str], targets: dict[str, str]) -> None:
    """Register substitutions and link targets with docutils.
    
    This function adds substitutions and link targets to the docutils parser's
    substitution_defs and targets dictionaries. This allows docutils to recognize
    these substitutions and targets when parsing RST files.
    
    :param substitutions: Dictionary of substitution names and their values
    :param targets: Dictionary of target names and their values
    """
    logger.debug("Registering %d substitutions and %d targets with docutils", 
                 len(substitutions), len(targets))
    
    # Register each substitution as a custom role
    for name, value in substitutions.items():
        logger.debug("Registering substitution: |%s| -> %s", name, value)
        register_substitution_handler(name, value)


class CodeBlockDirective(docutils.parsers.rst.Directive):
    """Code block directive."""

    has_content = True
    optional_arguments = 1

    def run(self) -> list[docutils.nodes.literal_block]:
        """Run directive.

        :return: Literal block
        """
        try:
            language = self.arguments[0]
        except IndexError:
            language = ""
        code = "\n".join(self.content)
        literal = docutils.nodes.literal_block(code, code)
        literal["classes"].append("code-block")
        literal["language"] = language
        return [literal]


def register_code_directive(
    *,
    ignore_code_directive: bool = False,
    ignore_codeblock_directive: bool = False,
    ignore_sourcecode_directive: bool = False,
) -> None:
    """Optionally register code directives.

    :param ignore_code_directive: If "code" directive should be ignored,
        so that the code block will not be checked; defaults to :py:obj:`False`
    :param ignore_codeblock_directive: If "code-block" directive should be ignored,
        so that the code block will not be checked; defaults to :py:obj:`False`
    :param ignore_sourcecode_directive: If "sourcecode" directive should be ignored,
        so that the code block will not be checked; defaults to :py:obj:`False`
    """
    if not _extras.SPHINX_INSTALLED:
        if ignore_code_directive is False:
            logger.debug("Register custom directive for 'code'.")
            docutils.parsers.rst.directives.register_directive("code", CodeBlockDirective)
        # NOTE: docutils maps `code-block` and `sourcecode` to `code`
        if ignore_codeblock_directive is False:
            logger.debug("Register custom directive for 'code-block'.")
            docutils.parsers.rst.directives.register_directive("code-block", CodeBlockDirective)
        if ignore_sourcecode_directive is False:
            logger.debug("Register custom directive for 'sourcecode'.")
            docutils.parsers.rst.directives.register_directive("sourcecode", CodeBlockDirective)


# Custom substitution handler for combined substitution and link references
def handle_substitution_reference(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: docutils.parsers.rst.states.Inliner,
    options: t.Mapping[str, t.Any] | None = None,
    content: t.Sequence[str] | None = None,
) -> tuple[list[docutils.nodes.Node], list[docutils.nodes.system_message]]:
    """Handle substitution references.
    
    This function is used to handle substitution references in RST files.
    It creates a substitution node with the given name and text.
    
    :param name: The name of the substitution
    :param rawtext: The raw text of the substitution reference
    :param text: The text of the substitution
    :param lineno: The line number of the substitution reference
    :param inliner: The inliner object
    :param options: Options for the substitution
    :param content: Content for the substitution
    :return: A tuple of nodes and system messages
    """
    logger.debug("Handling substitution reference: |%s|", name)
    options = options or {}
    content = content or []
    
    # Create a text node with the substitution text
    node = docutils.nodes.Text(text)
    
    return [node], []


# Register a custom substitution handler
def register_substitution_handler(name: str, text: str) -> None:
    """Register a custom substitution handler.
    
    This function registers a custom substitution handler for the given name.
    The handler will replace the substitution reference with the given text.
    
    :param name: The name of the substitution
    :param text: The text to replace the substitution with
    """
    logger.debug("Registering substitution handler for: |%s|", name)
    
    # Create a handler function that returns the given text
    def handler(
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner: docutils.parsers.rst.states.Inliner,
        options: t.Mapping[str, t.Any] | None = None,
        content: t.Sequence[str] | None = None,
    ) -> tuple[list[docutils.nodes.Node], list[docutils.nodes.system_message]]:
        return [docutils.nodes.Text(text)], []
    
    # Register the handler as a role
    docutils.parsers.rst.roles.register_local_role(f"substitution-{name}", handler)
