"""
Tests for the main CLI entry point.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import cast
from unittest.mock import Mock, patch

import pytest
from _pytest.capture import CaptureFixture
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from torrent.cli.main import main, setup_logging


def test_setup_logging_default() -> None:
    """Test default logging setup."""
    setup_logging()
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0], logging.StreamHandler)


def test_setup_logging_verbose() -> None:
    """Test verbose logging setup."""
    setup_logging(verbose=True)
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    handler = root_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    formatter = handler.formatter
    assert formatter is not None
    assert isinstance(formatter, logging.Formatter)
    fmt = cast(str, formatter._fmt)  # Cast to str since we know it's not None
    assert "%(levelname)s" in fmt


def test_setup_logging_with_file(tmp_path: Path) -> None:
    """Test logging setup with file output."""
    log_file = str(tmp_path / "test.log")
    setup_logging(log_file=log_file)
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 2
    assert any(isinstance(h, logging.FileHandler) for h in root_logger.handlers)


@patch("torrent.cli.main.process_single")
def test_main_file_command_with_all_options(mock_process: Mock) -> None:
    """Test main function with file command and all options."""
    mock_process.return_value = 0
    args = [
        "-v",
        "--log-file", "test.log",
        "--dry-run",
        "file",
        "path/to/content",
        "http://tracker.com/announce",
        "--min-piece-size", "256K",
        "--max-piece-size", "32M",
        "--target-pieces", "1000-2000",
        "--include-system",
        "--private",
        "-o", "output.torrent",
        "--force"
    ]

    assert main(args) == 0
    mock_process.assert_called_once()
    args_list, kwargs = mock_process.call_args
    assert kwargs["dry_run"]
    assert kwargs["force"]
    assert args_list[2] == "output.torrent"  # Check output parameter in positional args


@patch("torrent.cli.main.process_batch")
def test_main_batch_command_with_all_options(mock_process: Mock, tmp_path: Path) -> None:
    """Test batch command with all options."""
    directory = tmp_path / "input"
    directory.mkdir()
    output_dir = tmp_path / "output"

    mock_process.return_value = 0

    args = [
        "-v",
        "--dry-run",
        "batch",
        str(directory),
        "http://tracker.com/announce",
        "--min-piece-size", "256K",
        "--max-piece-size", "32M",
        "--target-pieces", "1000-2000",
        "--include-system",
        "--public",
        "-o", str(output_dir),
        "--clean",
        "--force",
        "--max-failures", "5"
    ]

    result = main(args)

    assert result == 0
    mock_process.assert_called_once()

    # Get positional and keyword arguments
    args, kwargs = mock_process.call_args
    assert args[0] == str(directory)  # First positional arg is directory
    assert kwargs["output_dir"] == str(output_dir)
    assert kwargs["force"]
    assert kwargs["clean"]
    assert kwargs["dry_run"]
    assert kwargs["max_failures"] == 5


@patch("torrent.cli.main.create_torrent_config")
def test_main_config_error(mock_config: Mock) -> None:
    """Test main function handling config error."""
    mock_config.side_effect = ValueError("Test error")
    args = ["file", "path/to/content", "http://tracker.com/announce"]

    assert main(args) == 1


@patch("torrent.cli.main.process_single")
def test_main_command_error(mock_process: Mock) -> None:
    """Test main function handling command error."""
    mock_process.side_effect = Exception("Test error")
    args = ["file", "path/to/content", "http://tracker.com/announce"]

    assert main(args) == 1


def test_main_invalid_command() -> None:
    """Test main function with invalid command."""
    args = ["invalid"]
    with pytest.raises(SystemExit) as exc_info:
        main(args)
    assert exc_info.value.code == 2


@patch("torrent.cli.main.process_single")
def test_main_verbose_error_handling(
    mock_process: Mock, caplog: LogCaptureFixture, capsys: CaptureFixture[str]
) -> None:
    """Test verbose error handling in main function."""
    mock_process.side_effect = Exception("Test error")
    args = ["--verbose", "file", "path/to/content", "http://tracker.com/announce"]

    with caplog.at_level(logging.DEBUG):
        assert main(args) == 1
        captured = capsys.readouterr()
        assert "Unexpected error: Test error" in captured.err
        assert "Traceback" in captured.err


@patch("torrent.cli.main.process_batch")
def test_main_batch_command_with_output_dir(mock_process: Mock, tmp_path: Path) -> None:
    """Test batch command with output directory manifest handling."""
    directory = tmp_path / "input"
    directory.mkdir()
    output_dir = tmp_path / "output"

    mock_process.return_value = 0

    result = main(
        ["batch", str(directory), "http://tracker.example.com", "-o", str(output_dir)]
    )

    assert result == 0
    mock_process.assert_called_once()

    # Get positional and keyword arguments
    args, kwargs = mock_process.call_args
    assert args[0] == str(directory)  # First positional arg is directory
    assert kwargs["output_dir"] == str(output_dir)
    assert not kwargs["force"]
    assert not kwargs["clean"]
