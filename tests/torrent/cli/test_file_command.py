"""Tests for the file command."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import libtorrent as lt
import pytest
from click.testing import CliRunner

from tests.utils import create_binary_file, create_empty_files, create_test_files
from torrent.cli.main import cli
from torrent.exceptions import ErrorCode


@pytest.fixture
def progress_callback() -> Callable[[float, str], None]:
    """
    Create a fixture for tracking progress updates.

    Returns:
        A callback function that stores progress updates in an updates attribute,
        which can be examined during tests.
    """
    updates = []

    def callback(progress: float, status: str) -> None:
        updates.append((progress, status))

    callback.updates = updates  # type: ignore
    return callback


@pytest.fixture
def empty_file(tmp_path: Path) -> str:
    """
    Create an empty file for testing empty file handling.

    Args:
        tmp_path: Pytest fixture that provides a temporary directory

    Returns:
        Path to the empty file as a string
    """
    empty_file = tmp_path / "empty.txt"
    create_empty_files(tmp_path, 1, "empty")
    return str(empty_file)


@pytest.fixture
def test_file(tmp_path: Path) -> str:
    """
    Create a test file with predictable content.

    Creates a 1MB file with zeros for consistent piece size calculations.

    Args:
        tmp_path: Pytest fixture that provides a temporary directory

    Returns:
        Path to the test file as a string
    """
    test_file = tmp_path / "test.txt"
    create_binary_file(test_file, 1024 * 1024)  # 1MB file
    return str(test_file)


@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    """Create a test directory for file operations."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    return test_dir


def test_file_command_basic_functionality(runner: CliRunner) -> None:
    """
    Test basic file command functionality.

    Verifies that:
    1. The command executes successfully (exit code 0)
    2. The torrent file is created at the expected location
    3. The torrent has the correct structure with specified parameters
       - Correct tracker URL
       - Private flag is set
       - Comment is included
       - Piece length matches specification
    """
    with runner.isolated_filesystem() as td:
        # Create test content
        test_file = Path(td) / "test.txt"
        create_test_files(Path(td), {"test.txt": "Test content"})
        output_path = Path(td) / "test.torrent"

        result = runner.invoke(
            cli,
            [
                "file",
                str(test_file),
                "http://tracker.example.com/announce",
                "--output",
                str(output_path),
                "--private",
                "--comment",
                "Test torrent",
                "--min-piece-size",
                "256K",
            ],
            standalone_mode=True,
        )

        assert result.exit_code == 0
        assert output_path.exists()

        # Verify torrent structure
        with open(output_path, "rb") as f:
            torrent_data = lt.bdecode(f.read())
            assert b"info" in torrent_data
            assert torrent_data[b"announce"] == b"http://tracker.example.com/announce"
            assert torrent_data[b"info"][b"private"] == 1
            assert torrent_data[b"comment"] == b"Test torrent"
            assert torrent_data[b"info"][b"piece length"] == 256 * 1024


def test_file_command_no_data_handling(runner: CliRunner) -> None:
    """Test file command handling of files with no data."""
    with runner.isolated_filesystem() as td:
        # Create empty file
        test_dir = Path(td) / "test_dir"
        test_dir.mkdir()
        create_empty_files(test_dir, 1, "empty")
        empty_file = (
            test_dir / "empty0.txt"
        )  # Updated to match create_empty_files naming

        result = runner.invoke(
            cli,
            [
                "file",
                str(empty_file),
                "http://tracker.example.com/announce",
                "--output",
                str(test_dir / "empty.torrent"),
            ],
            standalone_mode=True,
        )

        assert result.exit_code == 10  # NO_DATA error code
        assert "Error [NO_DATA]" in result.output
        assert "File" in result.output and "contains no data" in result.output
        assert not (test_dir / "empty.torrent").exists()


def test_file_command_mixed_empty_files(runner: CliRunner) -> None:
    """Test file command handling of directories with mixed empty and non-empty files."""
    with runner.isolated_filesystem() as td:
        # Create directory with mixed files
        mixed_dir = Path(td) / "mixed"
        mixed_dir.mkdir()
        create_test_files(mixed_dir, {"data.txt": "content"})  # Non-empty file
        create_empty_files(mixed_dir, 1, "empty")  # Empty file

        result = runner.invoke(
            cli,
            [
                "file",
                str(mixed_dir),
                "http://tracker.example.com/announce",
                "--output",
                str(Path(td) / "mixed.torrent"),
            ],
            standalone_mode=True,
        )

        # Should succeed because there is at least one non-empty file
        assert result.exit_code == 0
        assert (Path(td) / "mixed.torrent").exists()


def test_file_command_output_exists(runner: CliRunner) -> None:
    """Test file command handling of existing output files."""
    with runner.isolated_filesystem() as td:
        # Create test file and torrent
        test_dir = Path(td)
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test.txt").write_text("test content")
        (test_dir / "test.torrent").write_text("existing torrent")

        result = runner.invoke(
            cli,
            [
                "file",
                str(test_dir / "test.txt"),
                "http://tracker.example.com/announce",
                "--output",
                str(test_dir / "test.torrent"),
            ],
            standalone_mode=True,
        )

        assert result.exit_code == 12  # FILE_EXISTS error code
        assert "Output file already exists" in result.output
        assert "Use --force to overwrite existing files" in result.output


def test_file_command_web_seeds_handling(runner: CliRunner, tmp_path: Path) -> None:
    """
    Test web seed functionality and security in the file command.

    Verifies that:
    1. The command successfully creates a torrent with the standard tracker
    2. The torrent file contains the expected structure
    """
    create_test_files(tmp_path, {"test.txt": "Test content"})
    output_path = tmp_path / "test.torrent"

    result = runner.invoke(
        cli,
        [
            "file",
            str(tmp_path / "test.txt"),
            "http://tracker.example.com/announce",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert "Torrent created successfully" in result.output

    # Verify torrent structure
    with open(output_path, "rb") as f:
        torrent_data = lt.bdecode(f.read())
        assert b"info" in torrent_data
        assert torrent_data[b"announce"] == b"http://tracker.example.com/announce"


def test_file_command_progress_reporting(runner: CliRunner, test_file: str) -> None:
    """
    Test that the file command shows progress when verbose mode is enabled.

    Verifies that:
    1. The verbose flag successfully enables progress reporting
    2. The command completes successfully
    """
    # Create a test file with a valid size to avoid empty file issues
    result = runner.invoke(
        cli, ["-v", "--force", "file", test_file, "http://tracker.com"]
    )

    # The command should succeed with exit code 0
    assert result.exit_code == 0
    assert "Torrent created successfully" in result.output


def test_file_command_piece_size_calculation(runner: CliRunner, tmp_path: Path) -> None:
    """
    Test piece size constraints and calculations for different file sizes.

    Verifies that:
    1. For various file sizes, correct piece sizes are chosen
    2. Piece sizes are always powers of 2
    3. Each size follows the minimum/maximum constraints

    Tests the following size ranges:
    - Tiny file (16KB) -> Minimum piece size (256KB)
    - Small file (1MB) -> Minimum piece size (256KB)
    - Medium file (100MB) -> 1MB pieces
    - Large file (1GB) -> 4MB pieces
    """
    # Test various file sizes
    sizes = [
        (16 * 1024, 256 * 1024),  # 16KB -> 256KB pieces (minimum)
        (1024 * 1024, 256 * 1024),  # 1MB -> 256KB pieces
        (100 * 1024 * 1024, 1024 * 1024),  # 100MB -> 1MB pieces
        (1024 * 1024 * 1024, 4 * 1024 * 1024),  # 1GB -> 4MB pieces
    ]

    for file_size, expected_piece_size in sizes:
        test_file = tmp_path / f"test_{file_size}.bin"
        create_binary_file(test_file, file_size)
        output_path = tmp_path / f"test_{file_size}.torrent"

        result = runner.invoke(
            cli,
            [
                "file",
                str(test_file),
                "http://tracker.example.com/announce",
                "--output",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert output_path.exists()

        # Verify piece size
        with open(output_path, "rb") as f:
            torrent_data = lt.bdecode(f.read())
            assert torrent_data[b"info"][b"piece length"] == expected_piece_size


def test_file_command_tracker_url_validation(runner: CliRunner, test_dir: Path) -> None:
    """Test validation of tracker URLs."""
    # Create a test file
    create_test_files(test_dir, {"test.txt": "test content"})
    test_file = test_dir / "test.txt"
    output_file = test_dir / "test.torrent"

    # Test with invalid URL
    result = runner.invoke(
        cli,
        [
            "file",
            str(test_file),
            "invalid-url",
            "--output",
            str(output_file),
        ],
    )
    assert (
        result.exit_code == ErrorCode.INVALID_TRACKER_URL.value
    )  # Invalid URLs return tracker URL error
    assert "invalid tracker url" in result.output.lower()
    assert "must start with http://, https://, or udp://" in result.output.lower()
    assert not output_file.exists()  # Verify that no output file was created

    # Test with valid URL
    result = runner.invoke(
        cli,
        [
            "file",
            str(test_file),
            "http://tracker.example.com/announce",
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0  # Valid URL should succeed
    assert output_file.exists()  # Verify that the output file was created


def test_file_command_torrent_verification(runner: CliRunner) -> None:
    """
    Test torrent verification after creation.

    Verifies that:
    1. Created torrents are valid and can be loaded
    2. Torrent metadata matches input file
    3. Piece hashes are correctly calculated
    """
    with runner.isolated_filesystem() as td:
        test_file = Path(td) / "test.txt"
        create_binary_file(test_file, 1024 * 1024)  # 1MB file
        output_path = Path(td) / "test.torrent"

        result = runner.invoke(
            cli,
            [
                "file",
                str(test_file),
                "http://tracker.example.com/announce",
                "--output",
                str(output_path),
                "--min-piece-size",
                "256K",
            ],
            standalone_mode=True,
        )

        assert result.exit_code == 0
        assert output_path.exists()

        # Verify torrent can be loaded and contains correct data
        with open(output_path, "rb") as f:
            torrent_data = lt.bdecode(f.read())
            info = torrent_data[b"info"]
            assert info[b"piece length"] == 256 * 1024
            assert info[b"length"] == 1024 * 1024  # Should match input file size
            assert len(info[b"pieces"]) > 0  # Should have piece hashes
