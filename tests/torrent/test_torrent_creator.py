"""Tests for torrent creation functionality."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import libtorrent as lt
import pytest

from torrent.torrent_creator import TorrentCreator
from torrent.utils.config import TorrentConfig

TRACKER_URL = "http://example.com/announce"


@pytest.fixture
def test_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_torrent_private_by_default(test_dir: str) -> None:
    """Test that created torrent files are private by default."""
    # Create a test file
    test_file = os.path.join(test_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("test content")

    # Create torrent with default config (private=True)
    output_path = os.path.join(test_dir, "output.torrent")
    config = TorrentConfig(tracker_url=TRACKER_URL)
    creator = TorrentCreator(config)
    creator.create(test_file, output_path)

    # Read the torrent file and verify it's private
    info = lt.torrent_info(output_path)
    assert info.priv(), "Torrent should be private by default"


def test_torrent_private_override(test_dir: str) -> None:
    """Test that private flag can be overridden to False."""
    # Create a test file
    test_file = os.path.join(test_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("test content")

    # Create torrent with private=False
    output_path = os.path.join(test_dir, "output.torrent")
    config = TorrentConfig(tracker_url=TRACKER_URL, private=False)
    creator = TorrentCreator(config)
    creator.create(test_file, output_path)

    # Read the torrent file and verify it's not private
    info = lt.torrent_info(output_path)
    assert not info.priv(), "Torrent should not be private when private=False"


def test_calculate_optimal_piece_size():
    """Test optimal piece size calculation."""
    config = TorrentConfig()
    creator = TorrentCreator(config)

    # Test small file (1 MiB)
    size = 1024 * 1024
    piece_size = creator.calculate_optimal_piece_size(size)
    assert piece_size >= config.min_piece_size
    assert piece_size <= config.max_piece_size
    assert size / piece_size <= config.target_pieces_max

    # Test medium file (100 MiB)
    size = 100 * 1024 * 1024
    piece_size = creator.calculate_optimal_piece_size(size)
    assert piece_size >= config.min_piece_size
    assert piece_size <= config.max_piece_size
    assert size / piece_size <= config.target_pieces_max

    # Test large file (10 GiB)
    size = 10 * 1024 * 1024 * 1024
    piece_size = creator.calculate_optimal_piece_size(size)
    assert piece_size >= config.min_piece_size
    assert piece_size <= config.max_piece_size
    assert size / piece_size <= config.target_pieces_max


def test_verify_torrent_file(tmp_path):
    """Test torrent file verification."""
    config = TorrentConfig()
    creator = TorrentCreator(config)

    # Test with valid torrent
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    output_path = str(tmp_path / "valid.torrent")
    creator.create(str(test_file), output_path)
    assert creator.verify_torrent_file(output_path)

    # Test with non-existent file
    assert not creator.verify_torrent_file(str(tmp_path / "nonexistent.torrent"))

    # Test with invalid torrent file
    invalid_path = str(tmp_path / "invalid.torrent")
    with open(invalid_path, "wb") as f:
        f.write(b"invalid data")
    assert not creator.verify_torrent_file(invalid_path)


def test_create_with_invalid_input(tmp_path):
    """Test creating a torrent with invalid input path."""
    config = TorrentConfig()
    creator = TorrentCreator(config)

    with pytest.raises(ValueError, match="Input path does not exist"):
        creator.create(str(tmp_path / "nonexistent"), str(tmp_path / "output.torrent"))


def test_create_with_directory(tmp_path):
    """Test creating a torrent from a directory."""
    config = TorrentConfig()
    creator = TorrentCreator(config)

    # Create test directory with files
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("content 1")
    (test_dir / "file2.txt").write_text("content 2")
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("content 3")

    # Create torrent
    output_path = str(tmp_path / "test.torrent")
    creator.create(str(test_dir), output_path)

    # Verify torrent was created and is valid
    assert creator.verify_torrent_file(output_path)
