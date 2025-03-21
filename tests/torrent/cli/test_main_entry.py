"""
Tests for the main CLI entry point.
"""

from __future__ import annotations

import sys
from unittest.mock import patch

from torrent.cli.main import main


def test_main_entry_success() -> None:
    """Test that the main entry point returns the correct exit code on success."""
    test_args = ["torrent-directories", "--version"]
    with patch.object(sys, "argv", test_args):
        result = main()
        assert result == 0


def test_main_entry_error() -> None:
    """Test that the main entry point returns the correct exit code on error."""
    test_args = ["torrent-directories", "--invalid-option"]
    with patch.object(sys, "argv", test_args):
        result = main()
        assert result == 1  # Click returns 1 for usage errors


def test_main_entry_error_handling() -> None:
    """Test that the main entry point handles errors gracefully."""
    # Test with nonexistent file
    test_args = ["torrent-directories", "file", "nonexistent.txt", "http://example.com"]
    with patch.object(sys, "argv", test_args):
        result = main()
        assert result != 0  # Should return non-zero for errors

    # Test with invalid command
    test_args = ["torrent-directories", "invalid_command"]
    with patch.object(sys, "argv", test_args):
        result = main()
        assert result != 0  # Should return non-zero for errors

    # Test with missing required argument
    test_args = ["torrent-directories", "file"]
    with patch.object(sys, "argv", test_args):
        result = main()
        assert result != 0  # Should return non-zero for errors
