"""
Tests for the command-line interface.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from torrent.cli.commands import TorrentConfig
from torrent.cli.exceptions import FileIsEmptyError, OutputFileExistsError
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
    assert "torrent-directories" in result.output


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


def test_dry_run_file(runner: CliRunner, test_dir: Path, mocker: MockerFixture) -> None:
    """Test dry run for file command."""
    # Mock TorrentCreator
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")
    mock_creator.return_value.create.return_value = "test.torrent"
    mock_creator.return_value.config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce"
    )

    result = runner.invoke(
        cli,
        [
            "--dry-run",
            "file",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "output.torrent"),
        ],
    )
    assert result.exit_code == 0
    assert "Dry run mode" in result.output
    assert not (test_dir / "output.torrent").exists()


def test_dry_run_batch(
    runner: CliRunner, test_dir: Path, mocker: MockerFixture
) -> None:
    """Test dry run for batch command."""
    # Mock TorrentCreator
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")
    mock_creator.return_value.create.return_value = "test.torrent"
    mock_creator.return_value.config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce"
    )

    result = runner.invoke(
        cli,
        [
            "--dry-run",
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "torrents"),
        ],
    )
    assert result.exit_code == 0
    assert "Dry run mode" in result.output
    assert not (test_dir / "torrents").exists()


def test_force_option(runner: CliRunner, test_dir: Path, mocker: MockerFixture) -> None:
    """Test force option."""
    # Mock TorrentCreator
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")
    mock_creator.return_value.create.side_effect = [
        "test.torrent",  # First call succeeds
        OutputFileExistsError("Output file exists"),  # Second call fails
        "test.torrent",  # Third call succeeds with force
    ]
    mock_creator.return_value.config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce"
    )

    # Create initial torrent
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

    # Try to overwrite without force
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
    assert result.exit_code != 0

    # Try to overwrite with force
    result = runner.invoke(
        cli,
        [
            "file",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "output.torrent"),
            "--force",
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


def test_max_failures_option(
    runner: CliRunner, test_dir: Path, mocker: MockerFixture
) -> None:
    """Test max failures option for batch command."""
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
            "--max-failures",
            "1",
        ],
    )
    assert result.exit_code == 0


def test_main_function(runner: CliRunner) -> None:
    """Test main function."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


def test_skip_empty_option(
    runner: CliRunner, test_dir: Path, mocker: MockerFixture
) -> None:
    """Test skip empty option."""
    # Create an empty file
    empty_file = test_dir / "empty.txt"
    empty_file.touch()

    # Mock TorrentCreator to raise FileIsEmptyError
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")
    mock_creator.return_value.create.side_effect = [FileIsEmptyError("empty.txt"), None]
    mock_creator.return_value.config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce"
    )

    # Test without skip-empty option
    result = runner.invoke(
        cli,
        [
            "file",
            str(empty_file),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "empty.torrent"),
        ],
    )
    assert result.exit_code != 0
    assert "empty.txt is empty (0 bytes)" in result.output

    # Test with skip-empty option
    result = runner.invoke(
        cli,
        [
            "file",
            str(empty_file),
            "http://tracker.example.com/announce",
            "--output",
            str(test_dir / "empty.torrent"),
            "--skip-empty",
        ],
    )
    assert result.exit_code == 0


def test_skip_empty_batch(
    runner: CliRunner, tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test batch command with skip-empty option."""
    test_dir = tmp_path / "test_empty_batch"
    test_dir.mkdir()
    empty_dir = test_dir / "empty_dir"
    empty_dir.mkdir()
    (empty_dir / "empty.txt").touch()
    (empty_dir / "nonempty.txt").write_text("content")

    # Create output directory
    output_dir = test_dir / "torrents"
    output_dir.mkdir()

    # Mock TorrentCreator to succeed since the directory is valid (has non-empty content)
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")
    expected_torrent_path = str(output_dir / "empty_dir.torrent")

    def create_mock_torrent(path: str, output_path: str) -> str:
        # Create a mock torrent file
        with open(output_path, "w") as f:
            f.write("mock torrent content")
        return output_path

    mock_creator.return_value.create.side_effect = create_mock_torrent
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
            str(output_dir),
            "--skip-empty",
        ],
    )
    assert result.exit_code == 0
    assert f"Created {expected_torrent_path}" in result.output
    assert (output_dir / "empty_dir.torrent").exists()


def test_skip_empty_batch_max_failures(
    runner: CliRunner, tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test batch command with max-failures limit when encountering empty directories."""
    test_dir = tmp_path / "test_empty_batch_max_failures"
    test_dir.mkdir()

    # Create 5 directories with different contents
    for i in range(5):
        dir_path = test_dir / f"dir{i}"
        dir_path.mkdir()

        if i in [1, 3]:  # dir1 and dir3 will have only empty files
            (dir_path / f"empty{i}.txt").touch()
            (dir_path / f"empty{i}_2.txt").touch()
        else:  # Other directories have non-empty content
            (dir_path / f"file{i}.txt").write_text(f"content{i}")

    # Create output directory
    output_dir = test_dir / "torrents"
    output_dir.mkdir()

    # Mock TorrentCreator to succeed for non-empty directories and fail for empty ones
    mock_creator = mocker.patch("torrent.cli.commands.TorrentCreator")

    def create_mock_torrent(path: str, output_path: str) -> str:
        # Check if the directory contains only empty files
        dir_path = Path(path)
        if any(f.stat().st_size > 0 for f in dir_path.iterdir() if f.is_file()):
            # Create a mock torrent file for non-empty directories
            with open(output_path, "w") as f:
                f.write("mock torrent content")
            return output_path
        else:
            # Raise FileIsEmptyError for empty directories
            raise FileIsEmptyError(f"{dir_path.name} contains only empty files")

    mock_creator.return_value.create.side_effect = create_mock_torrent
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
            str(output_dir),
            "--max-failures",
            "1",
        ],
    )
    assert (
        result.exit_code != 0
    )  # Should fail since empty files are treated as failures
    assert "Error: Stopping after" in result.output  # Check for the exact error message
    assert "dir3" in result.output  # First empty directory encountered
    assert (
        "contains only empty files" in result.output
    )  # Check for the empty files error message

    # Verify that a torrent was created for dir2 (which has non-empty content)
    dir2_torrent = output_dir / "dir2.torrent"
    assert dir2_torrent.exists(), "Torrent file for dir2 should exist"
    assert dir2_torrent.stat().st_size > 0, "Torrent file for dir2 should not be empty"

    # Verify that dir2 is listed in the manifest
    manifest_file = output_dir / "manifest.csv"
    assert manifest_file.exists(), "Manifest file should exist"

    with open(manifest_file) as f:
        manifest_content = f.read()
        assert (
            str(test_dir / "dir2") in manifest_content
        ), "dir2 should be listed in manifest"
        assert (
            "dir2.torrent" in manifest_content
        ), "dir2.torrent should be listed in manifest"

    # Now test with --skip-empty to verify all non-empty directories get processed
    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
            "--skip-empty",
            "--force",  # Add force to allow overwriting existing torrents
        ],
    )
    assert (
        result.exit_code == 0
    ), "Command should succeed when skipping empty directories"

    # Verify torrents were created for all non-empty directories
    for i in [0, 2, 4]:  # dir0, dir2, and dir4 have non-empty content
        torrent_path = output_dir / f"dir{i}.torrent"
        assert torrent_path.exists(), f"Torrent file for dir{i} should exist"
        assert (
            torrent_path.stat().st_size > 0
        ), f"Torrent file for dir{i} should not be empty"

    # Verify manifest contains all non-empty directories
    with open(manifest_file) as f:
        manifest_content = f.read()
        for i in [0, 2, 4]:
            assert (
                str(test_dir / f"dir{i}") in manifest_content
            ), f"dir{i} should be listed in manifest"
            assert (
                f"dir{i}.torrent" in manifest_content
            ), f"dir{i}.torrent should be listed in manifest"

    # Test without --force to verify directories are skipped
    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
            "--skip-empty",
        ],
    )
    assert (
        result.exit_code == 0
    ), "Command should succeed when skipping already processed directories"
    assert (
        "Already processed" in result.output
    ), "Output should indicate directories were skipped"


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
            "file",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_file),
            "--force",
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
    runner: CliRunner,
    test_dir: Path,
    mocker: MockerFixture,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """Test that --force option updates file timestamps and manifest entries for batch command."""
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

    # Create output directory
    output_dir = test_dir / "torrents"
    output_dir.mkdir()

    # First run - create initial torrents
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

    # Record initial timestamps
    initial_timestamps = {}
    manifest_file = output_dir / "manifest.csv"
    assert manifest_file.exists(), "Manifest file should exist"

    # Get initial file timestamps
    for torrent_file in output_dir.glob("*.torrent"):
        initial_timestamps[torrent_file.name] = {
            "mtime": torrent_file.stat().st_mtime,
            "ctime": torrent_file.stat().st_ctime,
        }

    # Get initial manifest content and directory paths
    initial_directories = set()
    print("\nInitial manifest content:")
    with open(manifest_file) as f:
        manifest_content = f.read()
        print(manifest_content)
        f.seek(0)  # Reset file pointer
        reader = csv.DictReader(f)
        for row in reader:
            initial_directories.add(row["directory_path"])

    # Run with --force to update files
    result = runner.invoke(
        cli,
        [
            "batch",
            str(test_dir),
            "http://tracker.example.com/announce",
            "--output",
            str(output_dir),
            "--force",
        ],
    )
    assert result.exit_code == 0

    # Verify files were overwritten and timestamps updated
    for torrent_file in output_dir.glob("*.torrent"):
        current_stats = torrent_file.stat()
        initial_stats = initial_timestamps[torrent_file.name]

        # Verify file was overwritten (new creation time)
        assert (
            current_stats.st_ctime > initial_stats["ctime"]
        ), f"Creation time for {torrent_file.name} should be updated"

        # Verify file was modified (new modification time)
        assert (
            current_stats.st_mtime > initial_stats["mtime"]
        ), f"Modification time for {torrent_file.name} should be updated"

    # Verify manifest entries were updated
    updated_directories = set()
    print("\nFinal manifest content:")
    with open(manifest_file) as f:
        manifest_content = f.read()
        print(manifest_content)
        f.seek(0)  # Reset file pointer
        reader = csv.DictReader(f)
        for row in reader:
            updated_directories.add(row["directory_path"])

    # Print summary of manifest entries
    print("\nSummary of manifest entries:")
    print(f"Number of unique directories: {len(updated_directories)}")
    print(f"Unique directories: {sorted(updated_directories)}")

    # Capture and display the output
    out, _ = capfd.readouterr()
    print("\nTest output:")
    print(out)

    # Verify the same directories are present
    assert (
        initial_directories == updated_directories
    ), "Same directories should be present in manifest"

    # Verify all torrent files still exist
    for torrent_file in output_dir.glob("*.torrent"):
        assert (
            torrent_file.exists()
        ), f"Torrent file {torrent_file.name} should still exist"
        assert (
            torrent_file.stat().st_size > 0
        ), f"Torrent file {torrent_file.name} should not be empty"
