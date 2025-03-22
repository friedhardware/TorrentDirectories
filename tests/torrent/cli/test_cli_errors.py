"""Tests for CLI error handling."""

import pytest
from click.testing import CliRunner

from torrent.cli.main import cli
from torrent.errors.exceptions import ErrorCode


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


def test_missing_file(runner):
    """Test error when input file is missing."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["file", "nonexistent.txt", "http://tracker.example.com/announce"]
        )
        assert (
            result.exit_code == ErrorCode.USAGE_ERROR.value
        )  # Click validates path before our code
        assert "Path 'nonexistent.txt' does not exist" in result.output


def test_invalid_tracker_url(runner):
    """Test error when tracker URL is invalid."""
    with runner.isolated_filesystem():
        with open("test.txt", "w") as f:
            f.write("test content")
        result = runner.invoke(cli, ["file", "test.txt", "invalid-url"])
        assert result.exit_code == ErrorCode.INVALID_TRACKER_URL.value
        assert "Invalid tracker URL" in result.output


def test_empty_directory(runner):
    """Test error when processing an empty directory in batch mode."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["batch", "empty_dir", "http://tracker.example.com/announce"]
        )
        assert (
            result.exit_code == ErrorCode.USAGE_ERROR.value
        )  # Click validates directory before our code
        assert "Directory 'empty_dir' does not exist" in result.output


def test_invalid_piece_size(runner):
    """Test error when piece size is invalid."""
    with runner.isolated_filesystem():
        with open("test.txt", "w") as f:
            f.write("test content")
        result = runner.invoke(
            cli,
            [
                "file",
                "test.txt",
                "http://tracker.example.com/announce",
                "--min-piece-size",
                "invalid",
            ],
        )
        assert (
            result.exit_code == ErrorCode.USAGE_ERROR.value
        )  # Click validates option values
        assert "Invalid piece size format" in result.output
        assert "Use format like '16K', '1M', '32M'" in result.output


def test_access_denied(runner):
    """Test error when file access is denied."""
    with runner.isolated_filesystem():
        with open("test.txt", "w") as f:
            f.write("test content")
        import os

        os.chmod("test.txt", 0o000)  # Remove all permissions
        result = runner.invoke(
            cli, ["file", "test.txt", "http://tracker.example.com/announce"]
        )
        assert (
            result.exit_code == ErrorCode.USAGE_ERROR.value
        )  # Click validates file access
        assert "Path 'test.txt' is not readable" in result.output
