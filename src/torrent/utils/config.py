"""
Configuration classes for torrent creation and manifest management.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

# Constants for piece size limits
MIN_PIECE_SIZE = 16 * 1024  # 16 KiB
MAX_PIECE_SIZE = 64 * 1024 * 1024  # 64 MiB
DEFAULT_MAX_PIECE_SIZE = 16 * 1024 * 1024  # 16 MiB (default)
DEFAULT_MIN_PIECE_SIZE = 256 * 1024  # 256 KiB (default)


@dataclass
class TorrentConfig:
    """Configuration options for torrent creation."""
    
    # Piece size options
    min_piece_size: int = 16 * 1024  # 16 KiB
    max_piece_size: int = 16 * 1024 * 1024  # 16 MiB
    target_pieces_min: int = 1000
    target_pieces_max: int = 2000
    
    # File options
    skip_system_files: bool = True
    preserve_file_order: bool = False
    
    # Metadata options
    private: bool = False
    source: str | None = None
    comment: str | None = None
    
    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.min_piece_size <= 0:
            raise ValueError("min_piece_size must be positive")
        if self.max_piece_size <= 0:
            raise ValueError("max_piece_size must be positive")
        if self.min_piece_size > self.max_piece_size:
            raise ValueError("min_piece_size cannot be greater than max_piece_size")
        if self.target_pieces_min <= 0:
            raise ValueError("target_pieces_min must be positive")
        if self.target_pieces_max <= 0:
            raise ValueError("target_pieces_max must be positive")
        if self.target_pieces_min > self.target_pieces_max:
            raise ValueError("target_pieces_min cannot be greater than target_pieces_max")
    
    @property
    def target_pieces(self) -> tuple[int, int]:
        """Get the target number of pieces range."""
        return (self.target_pieces_min, self.target_pieces_max)

    def _is_power_of_2(self, n: int) -> bool:
        """Check if a number is a power of 2."""
        return n > 0 and (n & (n - 1)) == 0

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
        if not self._is_power_of_2(self.min_piece_size):
            raise ValueError(
                f"Minimum piece size must be a power of 2. Requested: {self.min_piece_size / 1024:.0f} KiB"
            )
        if not self._is_power_of_2(self.max_piece_size):
            raise ValueError(
                f"Maximum piece size must be a power of 2. Requested: {self.max_piece_size / 1024 / 1024:.0f} MiB"
            )
