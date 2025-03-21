"""Tests for the torrent creator module."""

from pathlib import Path

import pytest

from torrent.exceptions import NoDataError, OutputFileExistsError, TorrentCreationError
from torrent.torrent_creator import TorrentCreator
from torrent.utils.config import TorrentConfig


@pytest.fixture
def test_config() -> TorrentConfig:
    """Create a test config."""
    return TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=256 * 1024,  # 256 KiB
        max_piece_size=16 * 1024 * 1024,  # 16 MiB
        private=True,
        skip_hidden=True,
        skip_system_files=True,
    )


def test_create_torrent_from_file(tmp_path: Path, test_config: TorrentConfig) -> None:
    """Test creating a torrent from a single file."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # Create torrent
    creator = TorrentCreator(test_config)
    output_path = tmp_path / "test.torrent"
    creator.create(test_file, output_path)

    # Verify torrent was created
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_create_torrent_from_directory(
    tmp_path: Path, test_config: TorrentConfig
) -> None:
    """Test creating a torrent from a directory."""
    # Create test directory with files
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("test1")
    (test_dir / "file2.txt").write_text("test2")

    # Create torrent
    creator = TorrentCreator(test_config)
    output_path = tmp_path / "test.torrent"
    creator.create(test_dir, output_path)

    # Verify torrent was created
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_create_torrent_empty_file(tmp_path: Path, test_config: TorrentConfig) -> None:
    """Test creating a torrent from an empty file raises NoDataError."""
    # Create empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()

    # Attempt to create torrent
    creator = TorrentCreator(test_config)
    output_path = tmp_path / "empty.torrent"

    with pytest.raises(NoDataError):
        creator.create(empty_file, output_path)


def test_create_torrent_mixed_files(tmp_path: Path, test_config: TorrentConfig) -> None:
    """Test creating a torrent with both empty and non-empty files."""
    # Create test directory with mixed files
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "empty.txt").touch()
    (test_dir / "file1.txt").write_text("test1")

    # Create torrent
    creator = TorrentCreator(test_config)
    output_path = tmp_path / "test.torrent"
    creator.create(test_dir, output_path)

    # Verify torrent was created
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_create_torrent_file_exists(tmp_path: Path, test_config: TorrentConfig) -> None:
    """Test creating a torrent when output file already exists."""
    # Create test file and existing torrent
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    output_path = tmp_path / "test.torrent"
    output_path.touch()

    # Attempt to create torrent
    creator = TorrentCreator(test_config)
    with pytest.raises(OutputFileExistsError):
        creator.create(test_file, output_path)


def test_create_torrent_invalid_input(
    tmp_path: Path, test_config: TorrentConfig
) -> None:
    """Test creating a torrent with invalid input path."""
    creator = TorrentCreator(test_config)
    with pytest.raises(TorrentCreationError):
        creator.create(tmp_path / "nonexistent", tmp_path / "output.torrent")
