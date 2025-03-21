"""Tests for the TorrentConfig class."""

import pytest

from torrent.utils.config import TorrentConfig


def test_torrent_config_defaults() -> None:
    """Test default values for TorrentConfig."""
    config = TorrentConfig()
    assert config.min_piece_size == 256 * 1024  # 256 KiB default
    assert config.max_piece_size == 16 * 1024 * 1024  # 16 MiB default
    assert config.private is True
    assert config.comment == ""
    assert config.source == ""
    assert config.skip_hidden is True
    assert config.skip_system_files is True
    assert config.tracker_url is None


def test_torrent_config_custom_values() -> None:
    """Test setting custom values for TorrentConfig."""
    config = TorrentConfig(
        min_piece_size=256 * 1024,  # 256 KiB
        max_piece_size=1024 * 1024,  # 1 MiB
        private=False,
        comment="Test torrent",
        source="Test source",
        tracker_url="http://example.com/announce",
        skip_hidden=False,
        skip_system_files=False,
    )
    assert config.min_piece_size == 256 * 1024
    assert config.max_piece_size == 1024 * 1024
    assert config.private is False
    assert config.comment == "Test torrent"
    assert config.source == "Test source"
    assert config.tracker_url == "http://example.com/announce"
    assert config.skip_hidden is False
    assert config.skip_system_files is False


def test_torrent_config_invalid_piece_sizes() -> None:
    """Test setting invalid piece sizes."""
    # Test min piece size too small
    with pytest.raises(
        ValueError, match="Minimum piece size cannot be less than 16 KiB"
    ):
        TorrentConfig(min_piece_size=8 * 1024)  # 8 KiB

    # Test max piece size too large
    with pytest.raises(ValueError, match="Maximum piece size cannot exceed 64 MiB"):
        TorrentConfig(max_piece_size=128 * 1024 * 1024)  # 128 MiB

    # Test min > max piece size
    with pytest.raises(
        ValueError,
        match="Minimum piece size .* cannot be greater than maximum piece size",
    ):
        TorrentConfig(min_piece_size=2 * 1024 * 1024, max_piece_size=1024 * 1024)


def test_torrent_config_invalid_tracker_url() -> None:
    """Test setting invalid tracker URL."""
    with pytest.raises(ValueError, match="Invalid tracker URL"):
        TorrentConfig(tracker_url="not a url")
