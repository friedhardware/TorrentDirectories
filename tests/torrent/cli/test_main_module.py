"""
Tests for the main module entry point.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from torrent.cli.main import cli


def test_main_module_execution() -> None:
    """Test that the main module can be executed directly."""
    # Run the module through python -m
    result = subprocess.run(
        [sys.executable, "-m", "torrent.cli", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "version" in result.stdout.lower()


def test_main_module_error() -> None:
    """Test that the main module handles errors correctly."""
    # Run with invalid arguments
    result = subprocess.run(
        [sys.executable, "-m", "torrent.cli", "--invalid-option"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "error" in result.stderr.lower()


def test_main_module_help() -> None:
    """Test that the main module displays help information."""
    # Run with --help
    result = subprocess.run(
        [sys.executable, "-m", "torrent.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()
    assert "options" in result.stdout.lower()


def test_main_module_command() -> None:
    """Test that the main module can execute commands."""
    # Create a test directory
    test_dir = Path("test_main_module_command")
    test_dir.mkdir(exist_ok=True)
    try:
        # Run batch command with test directory
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "torrent.cli",
                "--dry-run",  # Global option must come before command
                "batch",
                str(test_dir),
                "http://example.com/announce",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "would process" in result.stdout.lower()  # Check dry-run output
    finally:
        # Clean up
        test_dir.rmdir()


def test_main_module_execution_mock() -> None:
    """Test main module execution."""
    with patch.object(sys, "argv", ["torrent-directories", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 0


def test_main_module_error_mock() -> None:
    """Test main module error handling."""
    with patch.object(sys, "argv", ["torrent-directories", "invalid"]):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code != 0


def test_main_module_help_mock() -> None:
    """Test main module help command."""
    with patch.object(sys, "argv", ["torrent-directories", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 0


def test_main_module_command_mock() -> None:
    """Test main module command execution."""
    with patch.object(sys, "argv", ["torrent-directories", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 0
