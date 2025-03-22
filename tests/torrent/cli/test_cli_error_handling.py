"""
Tests for CLI error handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from torrent.cli.main import cli
from torrent.errors.exceptions import ErrorCode


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def empty_file(tmp_path: Path) -> Path:
    """Create an empty file for testing."""
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    return empty_file


@pytest.fixture
def empty_dir(tmp_path: Path) -> Path:
    """Create an empty directory for testing."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    return empty_dir


def test_invalid_piece_size_format(runner: CliRunner, empty_file: Path) -> None:
    """Test error handling for invalid piece size format."""
    result = runner.invoke(
        cli,
        [
            "file",
            str(empty_file),
            "http://tracker.example.com/announce",
            "--min-piece-size",
            "123X",
        ],
    )
    assert result.exit_code == 2  # Click usage error
    assert "Invalid piece size format" in result.output
    assert "Use format like '16K', '1M', '32M'" in result.output


def test_min_piece_size_greater_than_max(runner: CliRunner, empty_file: Path) -> None:
    """Test error handling when min piece size is greater than max."""
    result = runner.invoke(
        cli,
        [
            "file",
            str(empty_file),
            "http://tracker.example.com/announce",
            "--min-piece-size",
            "32M",
            "--max-piece-size",
            "16M",
        ],
    )
    assert result.exit_code == 2  # Click usage error
    assert (
        "Minimum piece size (32768 KiB) cannot be greater than maximum piece size (16384 KiB)"
        in result.output
    )


def test_invalid_tracker_url(runner: CliRunner, empty_file: Path) -> None:
    """Test error code with invalid tracker URL."""
    result = runner.invoke(
        cli,
        [
            "file",
            str(empty_file),
            "invalid-url",
        ],
    )
    assert result.exit_code == ErrorCode.INVALID_TRACKER_URL.value
    assert "invalid tracker url" in result.output.lower()


def test_empty_file_error(runner: CliRunner, empty_file: Path) -> None:
    """Test error handling for empty file."""
    result = runner.invoke(
        cli, ["file", str(empty_file), "http://tracker.example.com/announce"]
    )
    assert result.exit_code == 10  # NO_DATA error code
    assert "Error [NO_DATA]" in result.output
    assert "contains no data" in result.output


def test_empty_directory_error(runner: CliRunner, tmp_path: Path) -> None:
    """Test error handling for empty directories."""
    # Create an empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = runner.invoke(
        cli, ["batch", str(empty_dir), "http://tracker.example.com/announce"]
    )
    assert result.exit_code == 11  # EMPTY_DIRECTORY error code
    assert "Parent directory is empty" in result.output
    assert "Directory must contain at least one non-empty file" in result.output


def test_nonexistent_file(runner: CliRunner) -> None:
    """Test error handling for non-existent file."""
    result = runner.invoke(
        cli, ["file", "nonexistent.txt", "http://tracker.example.com/announce"]
    )
    assert result.exit_code == 2  # Click usage error
    assert "Path 'nonexistent.txt' does not exist" in result.output


def test_file_in_batch_mode(runner: CliRunner, empty_file: Path) -> None:
    """Test error handling when using a file in batch mode."""
    result = runner.invoke(
        cli, ["batch", str(empty_file), "http://tracker.example.com/announce"]
    )
    assert result.exit_code == 2  # Click usage error
    assert f"Directory '{empty_file}' is a file" in result.output


def test_dry_run_output(runner: CliRunner, empty_file: Path) -> None:
    """Test dry run output format."""
    result = runner.invoke(
        cli,
        ["--dry-run", "file", str(empty_file), "http://tracker.example.com/announce"],
    )
    assert result.exit_code == 0
    assert "Would create torrent from:" in result.output
    assert "Would save to:" in result.output
    assert "Configuration:" in result.output
    assert "Private: True" in result.output


def test_batch_max_failures(runner: CliRunner, tmp_path: Path) -> None:
    """Test that batch mode respects the max failures limit."""
    parent = tmp_path / "parent"
    parent.mkdir()
    for i in range(3):
        empty_dir = parent / f"empty{i}"
        empty_dir.mkdir()

    # Test with max_failures=0 (no failures allowed)
    result = runner.invoke(
        cli,
        [
            "batch",
            str(parent),
            "http://tracker.example.com/announce",
            "--max-failures",
            "0",
        ],
    )
    assert result.exit_code == 24  # MAX_FAILURES_EXCEEDED error code
    assert "Maximum failures reached (1)" in result.output
    assert "Directory is empty: empty0" in result.output
    # Should not process other directories
    assert "empty1" not in result.output
    assert "empty2" not in result.output

    # Test with default max_failures (-1, unlimited)
    result = runner.invoke(
        cli, ["batch", str(parent), "http://tracker.example.com/announce"]
    )
    assert result.exit_code == 23  # BATCH_PROCESSING_ERROR
    assert "Directory is empty: empty0" in result.output
    assert "Directory is empty: empty1" in result.output
    assert "Directory is empty: empty2" in result.output


def test_batch_with_some_empty_directories(runner: CliRunner, tmp_path: Path) -> None:
    """Test batch mode with a mix of empty and non-empty directories."""
    parent = tmp_path / "parent"
    parent.mkdir()

    # Create one empty directory
    empty_dir = parent / "empty"
    empty_dir.mkdir()

    # Create one non-empty directory with a file
    non_empty_dir = parent / "non_empty"
    non_empty_dir.mkdir()
    test_file = non_empty_dir / "test.txt"
    test_file.write_text("test data")

    # Create output directory
    output_dir = tmp_path / "torrents"
    output_dir.mkdir()

    result = runner.invoke(
        cli,
        [
            "batch",
            str(parent),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
        ],
    )
    assert result.exit_code == 23  # BATCH_PROCESSING_ERROR
    assert "Directory is empty: empty" in result.output


def test_file_exists_error(runner: CliRunner, tmp_path: Path) -> None:
    """Test error handling when output file already exists."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test data")

    # Create the output torrent file that would conflict
    output_file = tmp_path / "test.txt.torrent"
    output_file.write_text("existing torrent")

    # First try without force (should fail)
    result = runner.invoke(
        cli,
        [
            "file",
            str(test_file),
            "--output",
            str(output_file),
            "http://tracker.example.com/announce",
        ],
    )
    assert result.exit_code == 12  # FILE_EXISTS error code
    assert "already exists" in result.output.lower()
    assert "Use --force to overwrite existing files" in result.output
    assert output_file.exists()  # File should still exist

    # Now try with force (should succeed)
    result = runner.invoke(
        cli,
        [
            "--force",
            "file",
            str(test_file),
            "--output",
            str(output_file),
            "http://tracker.example.com/announce",
        ],
    )
    assert result.exit_code == 0  # Success with --force
    assert output_file.exists()  # New file should be created


def test_verbose_error_output(runner: CliRunner, empty_file: Path) -> None:
    """Test error output in verbose mode."""
    result = runner.invoke(
        cli, ["-v", "file", str(empty_file), "http://tracker.example.com/announce"]
    )
    assert result.exit_code == 10  # NO_DATA error code
    assert "Error [NO_DATA]" in result.output
    # Verbose mode should include more details
    assert "Suggestion:" in result.output


def test_multiple_error_conditions(runner: CliRunner, tmp_path: Path) -> None:
    """Test handling of multiple error conditions at once."""
    result = runner.invoke(
        cli,
        [
            "file",
            "nonexistent.txt",  # Non-existent file
            "invalid_url",  # Invalid tracker URL
            "--min-piece-size",
            "32M",  # Invalid piece size combination
            "--max-piece-size",
            "16M",
        ],
    )
    # Should fail on the first error (non-existent file)
    assert result.exit_code == 2  # Click usage error
    assert "Path 'nonexistent.txt' does not exist" in result.output
    # Should not show other errors
    assert "Invalid tracker URL" not in result.output


def test_help_text_formatting(runner: CliRunner) -> None:
    """Test that help text is properly formatted."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Options:" in result.output
    assert "Commands:" in result.output

    # Test file command help
    result = runner.invoke(cli, ["file", "--help"])
    assert result.exit_code == 0
    assert "Create a torrent from a single file or directory" in result.output

    # Test batch command help
    result = runner.invoke(cli, ["batch", "--help"])
    assert result.exit_code == 0
    assert "Process all subdirectories in a parent directory" in result.output


def test_error_code_consistency(runner: CliRunner, tmp_path: Path) -> None:
    """Test that error codes are consistent across different error scenarios."""
    # Test empty directory error
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = runner.invoke(
        cli, ["batch", str(empty_dir), "http://tracker.example.com/announce"]
    )
    assert result.exit_code == 11  # EMPTY_DIRECTORY error code
    assert "Parent directory is empty" in result.output
    assert "Directory must contain at least one non-empty file" in result.output

    # Test file exists error
    test_file = tmp_path / "test.txt"
    test_file.write_text("test data")
    output_file = tmp_path / "test.txt.torrent"
    output_file.write_text("existing torrent")

    result = runner.invoke(
        cli,
        [
            "file",
            str(test_file),
            "http://tracker.example.com/announce",
            "-o",
            str(output_file),
        ],
    )
    assert result.exit_code == 12  # FILE_EXISTS error code
    assert "already exists" in result.output.lower()

    # Test no data error
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    result = runner.invoke(
        cli, ["file", str(empty_file), "http://tracker.example.com/announce"]
    )
    assert result.exit_code == 10  # NO_DATA error code
    assert "No data found" in result.output
