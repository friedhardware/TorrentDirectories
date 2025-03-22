"""
Tests for error handling utilities.
"""

from __future__ import annotations

import click
import pytest

from torrent.errors.error_handling import (
    _format_error_details,
    _get_error_help_text,
    convert_to_click_error,
    get_error_message,
)
from torrent.errors.exceptions import ErrorCode, TorrentError


def test_convert_to_click_error_with_details() -> None:
    """Test converting TorrentError with details to ClickException."""
    details = {
        "failed_files": ["file1.txt", "file2.txt"],
        "stats": {"processed": 10, "failed": 2},
        "simple_value": 42,
    }
    error = TorrentError(
        "Test error with details",
        error_code=ErrorCode.TORRENT_CREATION_ERROR,
        details=details,
    )
    click_error = convert_to_click_error(error)

    assert isinstance(click_error, click.ClickException)
    # Strip ANSI color codes for easier assertion
    message = (
        click_error.message.replace("\x1b[0m", "")
        .replace("\x1b[31m", "")
        .replace("\x1b[1m", "")
        .replace("\x1b[33m", "")
        .replace("\x1b[34m", "")
    )
    assert "Error [TORRENT_CREATION_ERROR]" in message
    assert "Test error with details" in message
    assert "Failed Files: \n  - file1.txt\n  - file2.txt" in message
    assert "Stats: \n  processed: 10\n  failed: 2" in message
    assert "Simple Value: 42" in message


def test_convert_to_click_error_non_torrent_error() -> None:
    """Test converting non-TorrentError exceptions to ClickException."""
    error = ValueError("Invalid value")
    click_error = convert_to_click_error(error)

    assert isinstance(click_error, click.ClickException)
    # Strip ANSI color codes for easier assertion
    message = (
        click_error.message.replace("\x1b[0m", "")
        .replace("\x1b[31m", "")
        .replace("\x1b[1m", "")
    )
    assert "Unexpected error: Invalid value" in message
    assert click_error.exit_code == ErrorCode.ERROR.value


def test_format_error_details_empty() -> None:
    """Test formatting empty error details."""
    assert _format_error_details({}) == ""
    assert _format_error_details({"empty_list": []}) == "Empty List: \n  - "
    assert _format_error_details({"empty_dict": {}}) == "Empty Dict: \n  "


def test_format_error_details_complex() -> None:
    """Test formatting complex error details."""
    details = {
        "nested_dict": {"key1": "value1", "key2": "value2"},
        "mixed_list": [1, "two", 3.0],
        "single_value": "test",
    }
    formatted = _format_error_details(details)

    assert "Nested Dict: \n  key1: value1\n  key2: value2" in formatted
    assert "Mixed List: \n  - 1\n  - two\n  - 3.0" in formatted
    assert "Single Value: test" in formatted


@pytest.mark.parametrize(
    "error_code,expected_message",
    [
        (
            ErrorCode.FILE_EXISTS,
            "Output file already exists.\nUse --force to overwrite existing files.",
        ),
        (
            ErrorCode.NO_DATA,
            "No data found to create torrent from.\nDirectory or file is empty.",
        ),
        (
            ErrorCode.MAX_FAILURES_EXCEEDED,
            "Maximum failures reached.\nUse --max-failures 0 to process all directories regardless of failures.",
        ),
        (ErrorCode.EMPTY_DIRECTORY, "Directory is empty."),
        (ErrorCode.NO_SUBDIRECTORIES, "No subdirectories found."),
        (
            ErrorCode.MISSING_TORRENT_FILES,
            "Found missing torrent files.\nUse --clean to remove invalid entries from manifest.",
        ),
        (ErrorCode.ERROR, "Generic error message"),  # Test fallback case
    ],
)
def test_get_error_message(error_code: ErrorCode, expected_message: str) -> None:
    """Test getting error messages for different error codes."""
    error = TorrentError("Generic error message", error_code=error_code)
    message = get_error_message(error)
    assert message == expected_message


def test_get_error_help_text_all_codes() -> None:
    """Test help text for all error codes."""
    for error_code in ErrorCode:
        error = TorrentError("Test error", error_code=error_code)
        help_text = _get_error_help_text(error)
        if error_code in [
            ErrorCode.NO_DATA,
            ErrorCode.EMPTY_DIRECTORY,
            ErrorCode.FILE_EXISTS,
            ErrorCode.NO_SUBDIRECTORIES,
            ErrorCode.MISSING_TORRENT_FILES,
            ErrorCode.MAX_FAILURES_EXCEEDED,
            ErrorCode.TORRENT_CREATION_ERROR,
            ErrorCode.INVALID_TRACKER_URL,
            ErrorCode.FILE_NOT_FOUND,
        ]:
            assert help_text != "", f"Help text missing for {error_code}"
        else:
            assert help_text == "", f"Unexpected help text for {error_code}"
