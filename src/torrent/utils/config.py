"""
Configuration classes for torrent creation and manifest management.
"""

from __future__ import annotations

from dataclasses import dataclass

# Constants for piece size limits
MIN_PIECE_SIZE = 16 * 1024  # 16 KiB
MAX_PIECE_SIZE = 64 * 1024 * 1024  # 64 MiB
DEFAULT_MAX_PIECE_SIZE = 16 * 1024 * 1024  # 16 MiB (default)
DEFAULT_MIN_PIECE_SIZE = 256 * 1024  # 256 KiB (default)


@dataclass
class TorrentConfig:
    """Configuration for torrent creation."""

    min_piece_size: int = DEFAULT_MIN_PIECE_SIZE
    max_piece_size: int = DEFAULT_MAX_PIECE_SIZE
    target_pieces_min: int = 1000
    target_pieces_max: int = 2000
    skip_hidden: bool = True
    skip_system_files: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.max_piece_size > MAX_PIECE_SIZE:
            raise ValueError(
                f"Maximum piece size cannot exceed 64 MiB. Requested: {self.max_piece_size / 1024 / 1024:.0f} MiB"
            )
        if self.min_piece_size < MIN_PIECE_SIZE:
            raise ValueError(
                f"Minimum piece size cannot be less than 16 KiB. Requested: {self.min_piece_size / 1024:.0f} KiB"
            )
        if self.min_piece_size > self.max_piece_size:
            raise ValueError(
                "Minimum piece size cannot be larger than maximum piece size"
            )
