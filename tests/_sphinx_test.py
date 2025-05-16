"""Tests for _sphinx module."""

from __future__ import annotations

import os
import pathlib
import tempfile
import textwrap

import pytest

from rstcheck_core import _sphinx


def test_extract_from_conf_py_with_custom_elements() -> None:
    """Test extract_from_conf_py with custom directives, roles, and substitutions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        conf_py_content = textwrap.dedent(
            """\
            # Configuration file for the Sphinx documentation builder.

            # -- Project information -----------------------------------------------------
            project = "Test Project"
            copyright = "2025, Test Author"
            author = "Test Author"

            # -- General configuration ---------------------------------------------------
            extensions = [
                "sphinx.ext.extlinks",
                "sphinx.ext.autodoc",
                "sphinx.ext.viewcode",
            ]

            # Custom roles and directives
            def setup(app):
                app.add_role("custom_role", lambda name, rawtext, text, lineno, inliner, options=None, content=None: ([], []))
                app.add_directive("custom_directive", lambda *args: None)

            # Extlinks configuration
            extlinks = {
                "github": ("https://github.com/%s", "%s"),
                "awsdocs": ("https://docs.aws.amazon.com/%s", "%s"),
                "codepkg": ("https://example.com/packages/%s", "%s"),
            }

            # Substitutions
            rst_epilog = '''
            .. |example| replace:: Example Text
            .. |test_sub| replace:: Test Substitution
            .. |product_name| replace:: Test Product
            '''

            # Additional substitutions
            custom_substitutions = {
                "version": "1.0.0",
                "release": "1.0.0",
            }
            """
        )
        conf_py_path = os.path.join(temp_dir, "conf.py")
        with open(conf_py_path, "w", encoding="utf-8") as f:
            f.write(conf_py_content)

        directives, roles, substitutions = _sphinx.extract_from_conf_py(temp_dir)

        # Check that custom directives are extracted
        assert "custom_directive" in directives
        
        # Check that common directives are included
        common_directives = ["toctree", "figure", "image", "note", "warning"]
        for directive in common_directives:
            if directive in directives:
                assert True
                break
        else:
            assert False, "No common directives found"

        # Check that custom roles are extracted
        assert "custom_role" in roles
        assert "github" in roles
        
        # Check that extlinks roles are extracted
        extlinks_roles = ["github", "issue", "pr"]
        for role in extlinks_roles:
            if role in roles:
                assert True
                break
        else:
            assert False, "No extlinks roles found"

        # Check that substitutions from rst_epilog are extracted
        assert "example" in substitutions
        assert "test_sub" in substitutions
        assert "product_name" in substitutions
        
        # Check that substitutions from custom_substitutions are extracted
        assert "version" in substitutions
        assert "release" in substitutions
        
        # Check that common substitutions are included
        common_subs = ["project", "copyright", "author"]
        for sub in common_subs:
            if sub in substitutions:
                assert True
                break
        else:
            assert False, "No common substitutions found"


def test_find_conf_py() -> None:
    """Test find_conf_py function."""
    # Test with a file in a directory with conf.py
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = pathlib.Path(temp_dir)
        conf_py_path = temp_dir_path / "conf.py"
        with open(conf_py_path, "w", encoding="utf-8") as f:
            f.write("# Test conf.py")

        test_file = temp_dir_path / "test.rst"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Test RST file")

        found_conf_dir = _sphinx.find_conf_py(test_file)
        assert found_conf_dir == str(temp_dir_path)

    # Test with a file in a directory without conf.py but with docs/source/conf.py
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = pathlib.Path(temp_dir)
        docs_source_path = temp_dir_path / "docs" / "source"
        docs_source_path.mkdir(parents=True)
        conf_py_path = docs_source_path / "conf.py"
        with open(conf_py_path, "w", encoding="utf-8") as f:
            f.write("# Test conf.py")

        test_file = temp_dir_path / "test.rst"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Test RST file")

        found_conf_dir = _sphinx.find_conf_py(test_file)
        assert found_conf_dir == str(docs_source_path)

    # Test with a file in a directory without conf.py
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = pathlib.Path(temp_dir)
        test_file = temp_dir_path / "test.rst"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Test RST file")

        found_conf_dir = _sphinx.find_conf_py(test_file)
        assert found_conf_dir is None

    # Test with None
    found_conf_dir = _sphinx.find_conf_py(None)
    assert found_conf_dir is None
