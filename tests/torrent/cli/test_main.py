"""
Tests for the command-line interface.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from torrent.cli.commands import TorrentConfig
from torrent.cli.main import cli


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def test_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a test directory with files and subdirectories."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Create test files
    for i in range(3):
        (test_dir / f"file{i}.txt").write_text(f"content{i}")

    # Create test subdirectories
    for i in range(3):
        subdir = test_dir / f"dir{i}"
        subdir.mkdir()
        (subdir / f"file{i}.txt").write_text(f"content{i}")

    yield test_dir


def test_version(runner: CliRunner) -> None:
    """Test version command."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


def test_help(runner: CliRunner) -> None:
    """Test help command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_file_command(runner: CliRunner, test_dir: Path) -> None:
    """Test file command."""
    result = runner.invoke(
        cli,
        [
            "file",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "output.torrent"),
        ],
    )
    assert result.exit_code == 0
    assert (test_dir / "output.torrent").exists()


def test_batch_command(
    runner: CliRunner, test_dir: Path, mocker: MockerFixture
) -> None:
    """Test batch command."""
    # Mock TorrentCreator
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")
    mock_creator.return_value.create.return_value = "test.torrent"
    mock_creator.return_value.config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce"
    )

    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "torrents"),
        ],
    )
    assert result.exit_code == 0
    assert (test_dir / "torrents").exists()


def test_force_option(runner: CliRunner, test_dir: Path) -> None:
    """Test that --force allows overwriting existing files."""
    # Create test file
    test_file = test_dir / "test.txt"
    test_file.write_text("test data")

    # Create existing torrent file
    output_file = test_dir / "test.torrent"
    output_file.write_text("existing torrent")

    # Try without force
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
    assert "Output file already exists" in result.output
    assert "Use --force to overwrite existing files" in result.output

    # Try with force
    result = runner.invoke(
        cli,
        [
            "--force",
            "file",
            str(test_file),
            "http://tracker.example.com/announce",
            "-o",
            str(output_file),
        ],
    )
    assert result.exit_code == 0


def test_clean_option(runner: CliRunner, test_dir: Path, mocker: MockerFixture) -> None:
    """Test clean option for batch command."""
    # Mock TorrentCreator
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")
    mock_creator.return_value.create.return_value = "test.torrent"
    mock_creator.return_value.config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce"
    )

    # Create initial torrents
    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "torrents"),
        ],
    )
    assert result.exit_code == 0

    # Run with clean option
    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "torrents"),
            "--clean",
        ],
    )
    assert result.exit_code == 0


def test_max_failures_option(runner: CliRunner, test_dir: Path) -> None:
    """Test max_failures option behavior."""
    # Create test directory with content
    content_dir = test_dir / "content_dir"
    content_dir.mkdir(exist_ok=True)
    (content_dir / "file.txt").write_text("content")

    # Create empty directory to trigger failure
    empty_dir = test_dir / "empty_dir"
    empty_dir.mkdir(exist_ok=True)

    # Create output directory
    output_dir = test_dir / "torrents"
    output_dir.mkdir(exist_ok=True)

    # Run with default max_failures (-1)
    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
        ],
        catch_exceptions=False,
    )
    assert (output_dir / "content_dir.torrent").exists()
    assert result.exit_code == 23  # BATCH_PROCESSING_ERROR
    assert "Failed to process" in result.output

    # Run with max_failures=0
    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
            "--max-failures",
            "0",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 24  # MAX_FAILURES_EXCEEDED
    assert "Maximum failures reached" in result.output


def test_main_function(runner: CliRunner) -> None:
    """Test main function."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


def test_force_updates_timestamps_file(
    runner: CliRunner, test_dir: Path, mocker: MockerFixture
) -> None:
    """Test that --force option updates file timestamps for single file command."""
    # Mock TorrentCreator
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")

    def create_mock_torrent(path: str, output_path: str) -> str:
        # Create a mock torrent file
        with open(output_path, "w") as f:
            f.write("mock torrent content")
        return output_path

    mock_creator.return_value.create.side_effect = create_mock_torrent
    mock_creator.return_value.config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce"
    )

    output_file = test_dir / "output.torrent"

    # First run - create initial torrent
    result = runner.invoke(
        cli,
        [
            "file",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert output_file.exists()

    # Record initial timestamps
    initial_stats = output_file.stat()
    initial_timestamps = {
        "mtime": initial_stats.st_mtime,
        "ctime": initial_stats.st_ctime,
    }

    # Run with --force to update file
    result = runner.invoke(
        cli,
        [
            "--force",
            "file",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0

    # Verify file was overwritten and timestamps updated
    current_stats = output_file.stat()

    # Verify file was overwritten (new creation time)
    assert (
        current_stats.st_ctime > initial_timestamps["ctime"]
    ), "Creation time should be updated"

    # Verify file was modified (new modification time)
    assert (
        current_stats.st_mtime > initial_timestamps["mtime"]
    ), "Modification time should be updated"

    # Verify file still exists and is not empty
    assert output_file.exists(), "Torrent file should still exist"
    assert output_file.stat().st_size > 0, "Torrent file should not be empty"


def test_force_updates_timestamps_batch(
    runner: CliRunner, test_dir: Path, mocker: MockerFixture
) -> None:
    """Test that --force option updates timestamps in batch mode."""
    # Mock TorrentCreator
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")

    def create_mock_torrent(path: str, output_path: str) -> str:
        # Create a mock torrent file
        with open(output_path, "w") as f:
            f.write("mock torrent content")
        return output_path

    mock_creator.return_value.create.side_effect = create_mock_torrent
    mock_creator.return_value.config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce"
    )

    # Create test directories
    for i in range(3):
        dir_path = test_dir / f"dir{i}"
        dir_path.mkdir(exist_ok=True)
        (dir_path / "file.txt").write_text(f"content {i}")

    # Create output directory
    output_dir = test_dir / "torrents"
    output_dir.mkdir(exist_ok=True)

    # First run to create initial torrents
    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Record initial timestamps
    initial_timestamps = {}
    for i in range(3):
        torrent_path = output_dir / f"dir{i}.torrent"
        initial_timestamps[f"dir{i}"] = torrent_path.stat().st_mtime

    # Wait a bit to ensure timestamps would be different
    time.sleep(1)

    # Force update
    result = runner.invoke(
        cli,
        [
            "--force",
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Check that timestamps were updated
    for i in range(3):
        torrent_path = output_dir / f"dir{i}.torrent"
        assert torrent_path.stat().st_mtime > initial_timestamps[f"dir{i}"]


def test_batch_command_basic(runner: CliRunner, test_dir: Path) -> None:
    """Test basic batch command functionality."""
    # Create test directories
    test_dir1 = test_dir / "test_dir1"
    test_dir1.mkdir()
    (test_dir1 / "file1.txt").write_text("content1")

    test_dir2 = test_dir / "test_dir2"
    test_dir2.mkdir()
    (test_dir2 / "file2.txt").write_text("content2")

    output_dir = test_dir / "torrents"
    output_dir.mkdir()

    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Created torrent for test_dir1" in result.output
    assert "Created torrent for test_dir2" in result.output
    assert (output_dir / "test_dir1.torrent").exists()
    assert (output_dir / "test_dir2.torrent").exists()


def test_batch_command_output_exists(runner: CliRunner, test_dir: Path) -> None:
    """Test batch command behavior when output file already exists."""
    # Create content and output directories
    content_dir = test_dir / "content"
    content_dir.mkdir()
    output_dir = test_dir / "output"
    output_dir.mkdir()

    # Create a subdirectory with content
    test_subdir = content_dir / "test_dir"
    test_subdir.mkdir()
    test_file = test_subdir / "test.txt"
    test_file.write_text("test content")

    # Create an existing torrent file
    existing_torrent = output_dir / "test_dir.torrent"
    existing_torrent.write_text("existing torrent")

    # Run batch command without --force
    result = runner.invoke(
        cli,
        [
            "batch",
            str(content_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
        ],
    )
    assert result.exit_code == 12  # FILE_EXISTS
    assert "Output file already exists" in result.output

    # Run batch command with --force
    result = runner.invoke(
        cli,
        [
            "--force",
            "batch",
            str(content_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0
    assert "Created torrent for test_dir" in result.output


def test_batch_command_max_failures(runner: CliRunner, test_dir: Path) -> None:
    """Test batch command with max failures option."""
    # Create test directory with content
    content_dir = test_dir / "content_dir"
    content_dir.mkdir(exist_ok=True)
    (content_dir / "file.txt").write_text("content")

    # Create empty directory to trigger failure
    empty_dir = test_dir / "empty_dir"
    empty_dir.mkdir(exist_ok=True)

    # Run with max_failures=0
    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "torrents"),
            "--max-failures",
            "0",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 24  # MAX_FAILURES_EXCEEDED
    assert "Maximum failures reached" in result.output
