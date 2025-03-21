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
        match="Maximum piece size .* cannot be less than minimum piece size",
    ):
        TorrentConfig(min_piece_size=2 * 1024 * 1024, max_piece_size=1024 * 1024)


def test_torrent_config_invalid_tracker_url() -> None:
    """Test setting invalid tracker URL."""
    with pytest.raises(ValueError, match="Invalid tracker URL"):
        TorrentConfig(tracker_url="not a url")


def test_set_piece_sizes_valid_values() -> None:
    """Test setting both piece sizes with valid values."""
    config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=256 * 1024,
        max_piece_size=16 * 1024 * 1024,
    )

    # Test setting to smaller valid values
    config.set_piece_sizes(min_size=16 * 1024, max_size=32 * 1024)
    assert config.min_piece_size == 16 * 1024
    assert config.max_piece_size == 32 * 1024

    # Test setting to larger valid values
    config.set_piece_sizes(min_size=1024 * 1024, max_size=16 * 1024 * 1024)
    assert config.min_piece_size == 1024 * 1024
    assert config.max_piece_size == 16 * 1024 * 1024


def test_set_piece_sizes_invalid_min() -> None:
    """Test that setting an invalid minimum piece size fails atomically."""
    config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=256 * 1024,
        max_piece_size=16 * 1024 * 1024,
    )

    original_min = config.min_piece_size
    original_max = config.max_piece_size

    # Try setting min piece size below minimum (16 KiB)
    with pytest.raises(ValueError, match="cannot be less than 16 KiB"):
        config.set_piece_sizes(min_size=8 * 1024, max_size=32 * 1024)

    # Verify both values remain unchanged
    assert config.min_piece_size == original_min
    assert config.max_piece_size == original_max


def test_set_piece_sizes_invalid_max() -> None:
    """Test that setting an invalid maximum piece size fails atomically."""
    config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=256 * 1024,
        max_piece_size=16 * 1024 * 1024,
    )

    original_min = config.min_piece_size
    original_max = config.max_piece_size

    # Try setting max piece size above maximum (64 MiB)
    with pytest.raises(ValueError, match="cannot exceed 64 MiB"):
        config.set_piece_sizes(min_size=16 * 1024, max_size=128 * 1024 * 1024)

    # Verify both values remain unchanged
    assert config.min_piece_size == original_min
    assert config.max_piece_size == original_max


def test_set_piece_sizes_min_greater_than_max() -> None:
    """Test that setting min_piece_size > max_piece_size fails atomically."""
    config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=256 * 1024,
        max_piece_size=16 * 1024 * 1024,
    )

    original_min = config.min_piece_size
    original_max = config.max_piece_size

    # Try setting min piece size greater than max
    with pytest.raises(ValueError, match="cannot be less than minimum piece size"):
        config.set_piece_sizes(min_size=32 * 1024, max_size=16 * 1024)

    # Verify both values remain unchanged
    assert config.min_piece_size == original_min
    assert config.max_piece_size == original_max


def test_set_piece_sizes_edge_cases() -> None:
    """Test edge cases for setting piece sizes."""
    config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=256 * 1024,
        max_piece_size=16 * 1024 * 1024,
    )

    # Test setting equal values (valid case)
    config.set_piece_sizes(min_size=32 * 1024, max_size=32 * 1024)
    assert config.min_piece_size == 32 * 1024
    assert config.max_piece_size == 32 * 1024

    # Test setting to minimum and maximum allowed values
    config.set_piece_sizes(min_size=256 * 1024, max_size=16 * 1024 * 1024)
    assert config.min_piece_size == 256 * 1024
    assert config.max_piece_size == 16 * 1024 * 1024


def test_piece_size_initialization_order() -> None:
    """Test piece size validation during initialization and direct property access."""
    # Test initialization order doesn't matter
    config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=16 * 1024,  # 16 KiB
        max_piece_size=32 * 1024,  # 32 KiB
    )
    assert config.min_piece_size == 16 * 1024
    assert config.max_piece_size == 32 * 1024

    # Test setting min_piece_size when max_piece_size hasn't been set
    config = TorrentConfig.__new__(TorrentConfig)
    config.tracker_url = "http://tracker.example.com/announce"

    # This should work since max_piece_size isn't set yet
    config._min_piece_size = 32 * 1024
    assert config._min_piece_size == 32 * 1024

    # Now set max_piece_size to a valid value
    config._max_piece_size = 64 * 1024
    assert config._max_piece_size == 64 * 1024

    # Test setting max_piece_size when min_piece_size hasn't been set
    config = TorrentConfig.__new__(TorrentConfig)
    config.tracker_url = "http://tracker.example.com/announce"

    # This should work since min_piece_size isn't set yet
    config._max_piece_size = 64 * 1024
    assert config._max_piece_size == 64 * 1024

    # Now set min_piece_size to a valid value
    config._min_piece_size = 32 * 1024
    assert config._min_piece_size == 32 * 1024


def test_set_piece_sizes_incremental_changes() -> None:
    """Test incrementally changing piece sizes in different orders."""
    config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=256 * 1024,  # 256 KiB
        max_piece_size=16 * 1024 * 1024,  # 16 MiB
    )

    # Test increasing max before min
    config.set_piece_sizes(min_size=512 * 1024, max_size=32 * 1024 * 1024)
    assert config.min_piece_size == 512 * 1024
    assert config.max_piece_size == 32 * 1024 * 1024

    # Test decreasing min before max
    config.set_piece_sizes(min_size=256 * 1024, max_size=16 * 1024 * 1024)
    assert config.min_piece_size == 256 * 1024
    assert config.max_piece_size == 16 * 1024 * 1024

    # Test setting to same values (no change)
    config.set_piece_sizes(min_size=256 * 1024, max_size=16 * 1024 * 1024)
    assert config.min_piece_size == 256 * 1024
    assert config.max_piece_size == 16 * 1024 * 1024


def test_set_piece_sizes_boundary_transitions() -> None:
    """Test transitions between boundary values for piece sizes."""
    config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=256 * 1024,
        max_piece_size=16 * 1024 * 1024,
    )

    # Test transition from min to max boundaries
    test_sizes = [
        (16 * 1024, 32 * 1024),  # Minimum valid
        (256 * 1024, 1024 * 1024),  # Common small
        (1024 * 1024, 16 * 1024 * 1024),  # Common medium
        (16 * 1024 * 1024, 64 * 1024 * 1024),  # Maximum valid
    ]

    for min_size, max_size in test_sizes:
        config.set_piece_sizes(min_size=min_size, max_size=max_size)
        assert config.min_piece_size == min_size
        assert config.max_piece_size == max_size


def test_tracker_url_validation() -> None:
    """Test tracker URL validation with various protocols."""
    # Test valid URLs
    valid_urls = [
        "http://tracker.example.com/announce",
        "https://secure.tracker.com/announce",
        "udp://tracker.example.com:6969/announce",
    ]
    for url in valid_urls:
        config = TorrentConfig(
            tracker_url=url,
            min_piece_size=256 * 1024,
            max_piece_size=16 * 1024 * 1024,
        )
        assert config.tracker_url == url

    # Test invalid URLs
    invalid_urls = [
        "ftp://tracker.example.com",  # Invalid protocol
        "not-a-url",  # No protocol
        "://invalid-url",  # Missing protocol
        "hxxp://tracker.example.com",  # Typo in protocol
    ]
    for url in invalid_urls:
        with pytest.raises(ValueError, match="Invalid tracker URL"):
            TorrentConfig(
                tracker_url=url,
                min_piece_size=256 * 1024,
                max_piece_size=16 * 1024 * 1024,
            )

    # Test None URL (valid for verification)
    config = TorrentConfig(
        tracker_url=None,
        min_piece_size=256 * 1024,
        max_piece_size=16 * 1024 * 1024,
    )
    assert config.tracker_url is None

    # Test URL modification after creation
    config = TorrentConfig(
        tracker_url="http://tracker1.example.com",
        min_piece_size=256 * 1024,
        max_piece_size=16 * 1024 * 1024,
    )
    config.tracker_url = "https://tracker2.example.com"  # Valid change
    assert config.tracker_url == "https://tracker2.example.com"

    with pytest.raises(ValueError, match="Invalid tracker URL"):
        config.tracker_url = "not-a-url"  # Invalid change


def test_piece_size_property_validation() -> None:
    """Test piece size property validation when accessing directly."""
    config = TorrentConfig(
        tracker_url="http://tracker.example.com/announce",
        min_piece_size=256 * 1024,
        max_piece_size=16 * 1024 * 1024,
    )

    # Test direct property access
    assert config.min_piece_size == 256 * 1024
    assert config.max_piece_size == 16 * 1024 * 1024

    # Test setting min_piece_size directly
    config.min_piece_size = 32 * 1024  # Valid
    assert config.min_piece_size == 32 * 1024

    with pytest.raises(ValueError, match="cannot be less than 16 KiB"):
        config.min_piece_size = 8 * 1024  # Too small

    with pytest.raises(ValueError, match="cannot be less than minimum piece size"):
        config.min_piece_size = 32 * 1024 * 1024  # Greater than max

    # Test setting max_piece_size directly
    config.max_piece_size = 32 * 1024 * 1024  # Valid
    assert config.max_piece_size == 32 * 1024 * 1024

    with pytest.raises(ValueError, match="cannot exceed 64 MiB"):
        config.max_piece_size = 128 * 1024 * 1024  # Too large

    with pytest.raises(ValueError, match="cannot be less than minimum piece size"):
        config.max_piece_size = 16 * 1024  # Less than min
