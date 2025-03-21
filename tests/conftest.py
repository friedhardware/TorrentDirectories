"""
Shared test configuration and fixtures.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator, Iterator, Optional

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from torrent.utils.config import TorrentConfig


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """
    Create a temporary directory for test files.

    Yields:
        Path to temporary directory that will be cleaned up after the test.
    """
    with tempfile.TemporaryDirectory() as temp:
        yield Path(temp)


@pytest.fixture
def sample_files(temp_dir: Path) -> Path:
    """
    Create a sample directory structure for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to the root of the sample directory structure
    """
    root = temp_dir / "sample"
    root.mkdir()

    # Create some regular files
    (root / "file1.txt").write_text("content1")
    (root / "file2.txt").write_text("content2")

    # Create a subdirectory with files
    subdir = root / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("content3")

    # Create some hidden files
    (root / ".hidden").write_text("hidden")
    (subdir / ".hidden_sub").write_text("hidden")

    # Create some system files
    (root / "Thumbs.db").write_text("system")
    (root / ".DS_Store").write_text("system")

    return root


@pytest.fixture
def default_config() -> TorrentConfig:
    """Create a TorrentConfig with default settings."""
    return TorrentConfig()


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """
    Provide a clean environment by temporarily clearing relevant env vars.

    This is useful for CLI tests where we don't want environment variables
    to affect the test behavior.
    """
    # Store original environment
    orig_env = {}
    vars_to_clear = [
        "TORRENT_MIN_PIECE_SIZE",
        "TORRENT_MAX_PIECE_SIZE",
        "TORRENT_SKIP_HIDDEN",
        "TORRENT_SKIP_SYSTEM",
    ]

    for var in vars_to_clear:
        if var in os.environ:
            orig_env[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original environment
    for var, value in orig_env.items():
        os.environ[var] = value


@pytest.fixture
def assert_logs(caplog: LogCaptureFixture) -> Generator[None, None, None]:
    """
    Helper fixture to assert log messages.

    This adds methods to the caplog fixture to make assertions about
    logged messages easier and more readable.

    Example:
        def test_something(assert_logs, caplog):
            with caplog.at_level(logging.INFO):
                do_something()
                assert "Expected message" in caplog.text
                assert caplog.has_error("error message")
    """

    def has_message(message: str, level: Optional[str] = None) -> bool:
        return any(
            message in record.message and (level is None or record.levelname == level)
            for record in caplog.records
        )

    caplog.has_debug = lambda msg: has_message(msg, "DEBUG")
    caplog.has_info = lambda msg: has_message(msg, "INFO")
    caplog.has_warning = lambda msg: has_message(msg, "WARNING")
    caplog.has_error = lambda msg: has_message(msg, "ERROR")

    yield


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """
    Automatically mark tests based on their location/name.

    This helps organize tests and allows running specific subsets:
        pytest -m cli  # Run only CLI tests
        pytest -m "not slow"  # Skip slow tests
    """
    for item in items:
        # Mark CLI tests
        if "cli" in str(item.fspath):
            item.add_marker(pytest.mark.cli)

        # Mark slow tests
        if "test_batch" in item.name or "test_integration" in item.name:
            item.add_marker(pytest.mark.slow)

        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
