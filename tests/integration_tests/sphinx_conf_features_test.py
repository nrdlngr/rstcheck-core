"""Test specific Sphinx conf.py features."""

from __future__ import annotations

import pathlib

import pytest

from rstcheck_core import checker


def test_sphinx_extlinks_support() -> None:
    """Test that Sphinx extlinks are properly supported."""
    # Path to the test file
    test_file = pathlib.Path("testing/examples/sphinx_conf/extlinks_test.rst")
    
    # Create a minimal config
    config = checker.config.RstcheckConfig()
    
    # Check the file
    errors = checker.check_file(test_file, config)
    
    # Verify that no errors are found
    assert not errors, f"Expected no errors, but found: {errors}"


def test_sphinx_substitutions_support() -> None:
    """Test that Sphinx substitutions are properly supported."""
    # Path to the test file
    test_file = pathlib.Path("testing/examples/sphinx_conf/substitutions_test.rst")
    
    # Create a minimal config
    config = checker.config.RstcheckConfig()
    
    # Check the file
    errors = checker.check_file(test_file, config)
    
    # Verify that no errors are found
    assert not errors, f"Expected no errors, but found: {errors}"
