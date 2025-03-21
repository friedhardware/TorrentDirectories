"""Tests for torrent verification functionality."""

from pathlib import Path

import pytest

from torrent.torrent_creator import TorrentCreator
from torrent.utils.config import TorrentConfig


@pytest.fixture
def temp_content(tmp_path: Path) -> Path:
    """Create temporary content for testing."""
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    test_file = content_dir / "test.txt"
    test_file.write_text("Test content")
    return content_dir


@pytest.fixture
def basic_config() -> TorrentConfig:
    """Create a basic torrent config."""
    return TorrentConfig(
        tracker_url="http://example.com/announce",
        private=True,
        source="test",
        comment="Test torrent",
        min_piece_size=16384,  # 16 KiB
        max_piece_size=16777216,  # 16 MiB
    )


def test_successful_verification(
    temp_content: Path, basic_config: TorrentConfig, tmp_path: Path
) -> None:
    """Test that a valid torrent passes verification."""
    creator = TorrentCreator(basic_config)
    output_path = str(tmp_path / "test.torrent")

    # Create the torrent
    creator.create(str(temp_content), output_path)

    # Verify the torrent - should not raise any exceptions
    result = creator.verify_torrent_file(output_path)
    assert result.success
    assert result.info_hash is not None
    assert result.piece_length is not None
    assert result.total_size is not None
    assert result.num_pieces is not None


def test_invalid_torrent_file(tmp_path: Path, basic_config: TorrentConfig) -> None:
    """Test that an invalid torrent file fails verification."""
    creator = TorrentCreator(basic_config)
    invalid_torrent = tmp_path / "invalid.torrent"

    # Create an invalid torrent file
    invalid_torrent.write_text("Not a valid torrent file")

    result = creator.verify_torrent_file(str(invalid_torrent))
    assert not result.success
    assert result.error is not None


def test_missing_torrent_file(tmp_path: Path, basic_config: TorrentConfig) -> None:
    """Test verification of a non-existent torrent file."""
    creator = TorrentCreator(basic_config)
    missing_path = tmp_path / "missing.torrent"

    result = creator.verify_torrent_file(str(missing_path))
    assert not result.success
    assert "No such file or directory" in result.error


def test_verification_error_handling(
    temp_content: Path, basic_config: TorrentConfig, tmp_path: Path
) -> None:
    """Test that verification errors are properly raised in the create method."""
    output_path = str(tmp_path / "test.torrent")

    # First create a torrent using process_single
    from torrent.cli.commands import process_single

    result = process_single(
        path=str(temp_content),
        tracker_url=basic_config.tracker_url,
        output=output_path,
        config=basic_config,
    )
    assert result == 0

    # Try creating a torrent at the same path without force
    # The process_single function now returns an error code instead of raising an exception
    result = process_single(
        path=str(temp_content),
        tracker_url=basic_config.tracker_url,
        output=output_path,
        config=basic_config,
    )
    assert result != 0

    # Now try with force=True
    result = process_single(
        path=str(temp_content),
        tracker_url=basic_config.tracker_url,
        output=output_path,
        config=basic_config,
        force=True,
    )
    assert result == 0

    # Verify the file was actually created and is valid
    creator = TorrentCreator(basic_config)
    result = creator.verify_torrent_file(output_path)
    assert result.success
    assert result.info_hash is not None
    assert result.piece_length is not None
    assert result.total_size is not None
    assert result.num_pieces is not None
