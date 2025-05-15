"""Test Sphinx conf.py support."""

from __future__ import annotations

import pathlib

from rstcheck_core import checker


def test_sphinx_conf_support() -> None:
    """Test that Sphinx conf.py features are supported."""
    # Path to the test file
    test_file = pathlib.Path("testing/examples/sphinx_conf/test_sphinx_conf.rst")
    
    # Create a minimal config
    config = checker.config.RstcheckConfig()
    
    # Check the file
    errors = checker.check_file(test_file, config)
    
    # Verify that no errors are found
    assert not errors, f"Expected no errors, but found: {errors}"


def test_without_sphinx_conf() -> None:
    """Test that files without conf.py still work correctly."""
    # Path to a test file that doesn't have a conf.py file
    test_file = pathlib.Path("testing/examples/good/rst.rst")
    
    # Create a minimal config
    config = checker.config.RstcheckConfig()
    
    # Check the file
    errors = checker.check_file(test_file, config)
    
    # Verify that no errors are found
    assert not errors, f"Expected no errors, but found: {errors}"
