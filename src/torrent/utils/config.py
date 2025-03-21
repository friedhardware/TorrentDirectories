"""
Configuration classes for torrent creation and manifest management.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Constants for piece size limits
MIN_PIECE_SIZE = 16 * 1024  # 16 KiB
MAX_PIECE_SIZE = 64 * 1024 * 1024  # 64 MiB
DEFAULT_MAX_PIECE_SIZE = 16 * 1024 * 1024  # 16 MiB (default)
DEFAULT_MIN_PIECE_SIZE = 256 * 1024  # 256 KiB (default)


@dataclass
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

    tracker_url: Optional[str] = (
        None  # Required for creation, optional for verification
    )
    min_piece_size: int = 256 * 1024  # 256 KiB
    max_piece_size: int = 16 * 1024 * 1024  # 16 MiB
    skip_hidden: bool = True
    skip_system_files: bool = True
    private: bool = True
    source: str = ""  # Empty string by default
    comment: str = ""  # Empty string by default

    def __post_init__(self) -> None:
        """Validate configuration values."""
        # Validate piece sizes
        if self.min_piece_size < 16 * 1024:  # 16 KiB
            raise ValueError(
                f"Minimum piece size cannot be less than 16 KiB. Requested: {self.min_piece_size / 1024:.0f} KiB"
            )
        if self.max_piece_size > 64 * 1024 * 1024:  # 64 MiB
            raise ValueError(
                f"Maximum piece size cannot exceed 64 MiB. Requested: {self.max_piece_size / 1024 / 1024:.0f} MiB"
            )
        if self.min_piece_size > self.max_piece_size:
            raise ValueError(
                f"Minimum piece size ({self.min_piece_size / 1024:.0f} KiB) cannot be greater than "
                f"maximum piece size ({self.max_piece_size / 1024:.0f} KiB)"
            )

        # Validate tracker URL if provided
        if self.tracker_url and not self.tracker_url.startswith(
            ("http://", "https://", "udp://")
        ):
            raise ValueError(
                f"Invalid tracker URL: {self.tracker_url}. Must start with http://, https://, or udp://"
            )
