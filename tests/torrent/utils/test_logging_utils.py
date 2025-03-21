"""
Tests for logging utilities.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Generator

import click
import pytest
from click.testing import CliRunner

from torrent.utils.logging_utils import log_batch_progress, log_progress, setup_logging


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner(mix_stderr=False)


@pytest.fixture(autouse=True)
def clean_logging() -> Generator[None, None, None]:
    """Clean up logging configuration before and after each test."""
    root_logger = logging.getLogger()
    old_level = root_logger.level
    old_handlers = root_logger.handlers[:]

    # Remove all handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    yield

    # Restore original state
    root_logger.setLevel(old_level)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    for handler in old_handlers:
        root_logger.addHandler(handler)


def test_setup_logging_default() -> None:
    """Test setup_logging with default settings."""
    setup_logging()
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO


def test_setup_logging_verbose() -> None:
    """Test setup_logging with verbose mode."""
    setup_logging(verbose=True)
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_setup_logging_with_file(tmp_path: Path) -> None:
    """Test setup_logging with a log file."""
    log_file = tmp_path / "test.log"
    setup_logging(log_file=str(log_file))
    root_logger = logging.getLogger()

    assert any(isinstance(h, logging.FileHandler) for h in root_logger.handlers)
    assert os.path.exists(log_file)

    # Test log message appears in file
    logging.info("Test message")
    with open(log_file, "r") as f:
        content = f.read()
        assert "Test message" in content


def test_setup_logging_removes_existing_handlers() -> None:
    """Test that setup_logging removes existing handlers."""
    root_logger = logging.getLogger()

    # Add a test handler
    test_handler = logging.StreamHandler()
    root_logger.addHandler(test_handler)

    setup_logging()

    assert test_handler not in root_logger.handlers


def test_log_progress_success(runner: CliRunner) -> None:
    """Test log_progress with success status."""

    @click.command()
    def cmd() -> None:
        log_progress("Operation completed")

    result = runner.invoke(cmd)
    assert result.exit_code == 0
    assert "Operation completed: ✓" in result.stdout


def test_log_progress_failure(runner: CliRunner) -> None:
    """Test log_progress with failure status."""

    @click.command()
    def cmd() -> None:
        log_progress("Operation failed", success=False)

    result = runner.invoke(cmd)
    assert result.exit_code == 0
    assert "Operation failed: ✗" in result.stdout


def test_log_batch_progress_new_torrent(runner: CliRunner) -> None:
    """Test log_batch_progress for newly created torrent."""

    @click.command()
    def cmd() -> None:
        log_batch_progress("test_dir", "test.torrent")

    result = runner.invoke(cmd)
    assert result.exit_code == 0
    assert "test_dir: Created test.torrent" in result.stdout


def test_log_batch_progress_already_processed(runner: CliRunner) -> None:
    """Test log_batch_progress for already processed directory."""

    @click.command()
    def cmd() -> None:
        log_batch_progress("test_dir")

    result = runner.invoke(cmd)
    assert result.exit_code == 0
    assert "test_dir: Already processed" in result.stdout


def test_log_progress_unicode_support(runner: CliRunner) -> None:
    """Test log_progress with Unicode characters."""

    @click.command()
    def cmd() -> None:
        log_progress("Unicode test 🚀")

    result = runner.invoke(cmd)
    assert result.exit_code == 0
    assert "Unicode test 🚀: ✓" in result.stdout


def test_log_batch_progress_unicode_paths(runner: CliRunner) -> None:
    """Test log_batch_progress with Unicode paths."""

    @click.command()
    def cmd() -> None:
        log_batch_progress("测试目录", "测试.torrent")

    result = runner.invoke(cmd)
    assert result.exit_code == 0
    assert "测试目录: Created 测试.torrent" in result.stdout


def test_setup_logging_file_permissions(tmp_path: Path) -> None:
    """Test setup_logging handles file permission issues gracefully."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "test.log"

    # Make directory read-only after creating it
    os.chmod(log_dir, 0o444)

    try:
        with pytest.raises(Exception):  # Should raise when can't write to file
            setup_logging(log_file=str(log_file))
    finally:
        # Restore permissions for cleanup
        os.chmod(log_dir, 0o755)
