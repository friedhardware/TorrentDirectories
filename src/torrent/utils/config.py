"""
Configuration classes for torrent creation and manifest management.
"""

from __future__ import annotations

from typing import Optional

# Constants for piece size limits
MIN_PIECE_SIZE = 16 * 1024  # 16 KiB
MAX_PIECE_SIZE = 64 * 1024 * 1024  # 64 MiB
DEFAULT_MAX_PIECE_SIZE = 16 * 1024 * 1024  # 16 MiB (default)
DEFAULT_MIN_PIECE_SIZE = 256 * 1024  # 256 KiB (default)


class TorrentConfig:
    """Configuration for torrent creation.

    Attributes:
        tracker_url: Tracker URL to use (required for creation, optional for verification)
        min_piece_size: Minimum piece size in bytes (must be >= 16 KiB)
        max_piece_size: Maximum piece size in bytes (must be <= 64 MiB)
        skip_hidden: Whether to skip hidden files
        skip_system_files: Whether to skip system files
        private: Whether to create private torrents
        source: Optional source string for the torrent
        comment: Optional comment string for the torrent
    """

    def __init__(
        self,
        tracker_url: Optional[str] = None,
        min_piece_size: int = DEFAULT_MIN_PIECE_SIZE,
        max_piece_size: int = DEFAULT_MAX_PIECE_SIZE,
        skip_hidden: bool = True,
        skip_system_files: bool = True,
        private: bool = True,
        source: str = "",
        comment: str = "",
    ) -> None:
        # Initialize protected attributes
        self._tracker_url: Optional[str] = None
        self._min_piece_size: int = DEFAULT_MIN_PIECE_SIZE
        self._max_piece_size: int = DEFAULT_MAX_PIECE_SIZE

        # Initialize basic attributes
        self.tracker_url = tracker_url  # Use property setter for validation
        self.skip_hidden = skip_hidden
        self.skip_system_files = skip_system_files
        self.private = private
        self.source = source
        self.comment = comment

        # Initialize piece sizes
        self.set_piece_sizes(min_piece_size, max_piece_size)

    def _validate_tracker_url(self, url: Optional[str]) -> None:
        """Validate tracker URL if provided."""
        if url and not url.startswith(("http://", "https://", "udp://")):
            raise ValueError(
                f"Invalid tracker URL: {url}. Must start with http://, https://, or udp://"
            )

    @property
    def tracker_url(self) -> Optional[str]:
        """Get tracker URL."""
        return self._tracker_url

    @tracker_url.setter
    def tracker_url(self, value: Optional[str]) -> None:
        """Set tracker URL with validation."""
        self._validate_tracker_url(value)
        self._tracker_url = value

    @property
    def min_piece_size(self) -> int:
        """Get minimum piece size."""
        return self._min_piece_size

    @min_piece_size.setter
    def min_piece_size(self, value: int) -> None:
        """Set minimum piece size with validation."""
        if value < MIN_PIECE_SIZE:
            raise ValueError(
                f"Minimum piece size cannot be less than 16 KiB. Requested: {value / 1024:.0f} KiB"
            )
        if hasattr(self, "_max_piece_size") and value > self._max_piece_size:
            raise ValueError(
                f"Maximum piece size ({self._max_piece_size / 1024:.0f} KiB) cannot be less than "
                f"minimum piece size ({value / 1024:.0f} KiB)"
            )
        self._min_piece_size = value

    @property
    def max_piece_size(self) -> int:
        """Get maximum piece size."""
        return self._max_piece_size

    @max_piece_size.setter
    def max_piece_size(self, value: int) -> None:
        """Set maximum piece size with validation."""
        if value > MAX_PIECE_SIZE:
            raise ValueError(
                f"Maximum piece size cannot exceed 64 MiB. Requested: {value / 1024 / 1024:.0f} MiB"
            )
        if hasattr(self, "_min_piece_size") and self._min_piece_size > value:
            raise ValueError(
                f"Maximum piece size ({value / 1024:.0f} KiB) cannot be less than "
                f"minimum piece size ({self._min_piece_size / 1024:.0f} KiB)"
            )
        self._max_piece_size = value

    def set_piece_sizes(self, min_size: int, max_size: int) -> None:
        """Set both minimum and maximum piece sizes with validation.

        Args:
            min_size: Minimum piece size in bytes (must be >= 16 KiB)
            max_size: Maximum piece size in bytes (must be <= 64 MiB)

        Raises:
            ValueError: If piece sizes are invalid or min_size > max_size
        """
        # Basic validation first
        if min_size < MIN_PIECE_SIZE:
            raise ValueError(
                f"Minimum piece size cannot be less than 16 KiB. Requested: {min_size / 1024:.0f} KiB"
            )
        if max_size > MAX_PIECE_SIZE:
            raise ValueError(
                f"Maximum piece size cannot exceed 64 MiB. Requested: {max_size / 1024 / 1024:.0f} MiB"
            )
        if min_size > max_size:
            raise ValueError(
                f"Maximum piece size ({max_size / 1024:.0f} KiB) cannot be less than "
                f"minimum piece size ({min_size / 1024:.0f} KiB)"
            )

        # Set both values atomically
        self._min_piece_size = min_size
        self._max_piece_size = max_size
