"""
Integration tests for CLI command handlers.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from torrent.cli.commands import process_batch, process_single
from torrent.utils.config import TorrentConfig


def create_test_files(directory: Path, file_count: int = 3) -> None:
    """Create test files in the given directory."""
    for i in range(file_count):
        (directory / f"file{i}.txt").write_text(f"content{i}")


@pytest.fixture
def sample_directory(tmp_path: Path) -> Path:
    """Create a sample directory with test files."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    create_test_files(test_dir)
    return test_dir


@pytest.fixture
def batch_directory(tmp_path: Path) -> Path:
    """Create a directory structure for batch processing."""
    parent_dir = tmp_path / "parent"
    parent_dir.mkdir()

    # Create multiple subdirectories with files
    for i in range(3):
        subdir = parent_dir / f"dir{i}"
        subdir.mkdir()
        create_test_files(subdir, file_count=2)

    return parent_dir


def test_process_single_integration(
    sample_directory: Path, tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    """Integration test for processing a single directory."""
    output_file = tmp_path / "output.torrent"
    config = TorrentConfig(
        min_piece_size=16384,  # Small piece size for testing
        max_piece_size=32768,
        private=True,
        source="test",
        comment="Test torrent",
    )

    result = process_single(
        str(sample_directory),
        "http://tracker.example.com/announce",
        str(output_file),
        config=config,
    )

    assert result == 0
    assert output_file.exists()
    assert "Torrent created successfully" in caplog.text

    # Verify the torrent file is valid by checking its size
    assert output_file.stat().st_size > 0


def test_process_batch_integration(
    batch_directory: Path, tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    """Integration test for batch processing multiple directories."""
    output_dir = tmp_path / "torrents"
    config = TorrentConfig(
        min_piece_size=16384,
        max_piece_size=32768,
        private=True,
        source="test",
        comment="Test torrent",
    )

    result = process_batch(
        str(batch_directory),
        "http://tracker.example.com/announce",
        config=config,
        output_dir=str(output_dir),
    )

    assert result == 0
    assert output_dir.exists()

    # Verify torrent files were created
    torrent_files = list(output_dir.glob("*.torrent"))
    assert len(torrent_files) == 3
    for torrent_file in torrent_files:
        assert torrent_file.stat().st_size > 0

    # Verify manifest file was created
    manifest_file = output_dir / "manifest.csv"
    assert manifest_file.exists()


def test_process_batch_incremental_integration(
    batch_directory: Path, tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    """Integration test for incremental batch processing."""
    output_dir = tmp_path / "torrents"
    config = TorrentConfig(min_piece_size=16384, max_piece_size=32768)

    # First run - process all directories
    result = process_batch(
        str(batch_directory),
        "http://tracker.example.com/announce",
        config=config,
        output_dir=str(output_dir),
    )
    assert result == 0
    initial_torrent_count = len(list(output_dir.glob("*.torrent")))

    # Add a new directory
    new_dir = batch_directory / "dir_new"
    new_dir.mkdir()
    create_test_files(new_dir)

    # Second run - should only process the new directory
    caplog.clear()
    result = process_batch(
        str(batch_directory),
        "http://tracker.example.com/announce",
        config=config,
        output_dir=str(output_dir),
    )

    assert result == 0
    assert len(list(output_dir.glob("*.torrent"))) == initial_torrent_count + 1
    assert "Already processed" in caplog.text


def test_process_batch_force_update_integration(
    batch_directory: Path, tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    """Integration test for forced batch processing update."""
    output_dir = tmp_path / "torrents"
    config = TorrentConfig(min_piece_size=16384, max_piece_size=32768)

    # First run - process all directories
    result = process_batch(
        str(batch_directory),
        "http://tracker.example.com/announce",
        config=config,
        output_dir=str(output_dir),
    )
    assert result == 0

    # Get initial timestamps of torrent files
    initial_timestamps = {
        f: os.path.getmtime(f)
        for f in output_dir.glob("*.torrent")
    }

    # Force update all torrents
    caplog.clear()
    result = process_batch(
        str(batch_directory),
        "http://tracker.example.com/announce",
        config=config,
        output_dir=str(output_dir),
        force=True,
    )

    assert result == 0
    # Verify all torrent files were updated
    for torrent_file in output_dir.glob("*.torrent"):
        assert os.path.getmtime(torrent_file) > initial_timestamps[torrent_file]


def test_process_single_large_files_integration(
    tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    """Integration test for processing large files."""
    test_dir = tmp_path / "large_files"
    test_dir.mkdir()

    # Create a few larger files (1MB each)
    for i in range(2):
        with open(test_dir / f"large_file{i}.dat", "wb") as f:
            f.write(os.urandom(1024 * 1024))  # 1MB of random data

    output_file = tmp_path / "large.torrent"
    config = TorrentConfig(
        min_piece_size=1024 * 1024,  # 1MB pieces for large files
        max_piece_size=2 * 1024 * 1024,  # 2MB max piece size
        private=True,
    )

    result = process_single(
        str(test_dir),
        "http://tracker.example.com/announce",
        str(output_file),
        config=config,
    )

    assert result == 0
    assert output_file.exists()
    assert output_file.stat().st_size > 0 