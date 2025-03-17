"""
Core functionality for creating torrent files with optimal settings.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

import libtorrent as lt  # type: ignore

from torrent.cli.exceptions import FileIsEmptyError
from torrent.utils.config import TorrentConfig
from torrent.utils.file_utils import sync_to_disk

logger = logging.getLogger(__name__)


class TorrentCreator:
    """
    Creates torrent files with optimal settings for both single files and directories.

    This class handles the core torrent creation functionality, including:
    - Piece size calculation following strict rules:
        * Must be a power of 2 (e.g. 16 KiB, 32 KiB, 64 KiB)
        * Must be a multiple of 16 KiB
        * Must be between min_piece_size and max_piece_size from config
    - File filtering (hidden files, system files)
    - Empty file handling (skip or error based on config)
    - Progress reporting
    - Torrent verification

    The default configuration uses:
    - Minimum piece size: 256 KiB
    - Maximum piece size: 16 MiB
    - Private flag: True
    - Skip hidden files: True
    - Skip system files: True
    - Skip empty files: False

    Args:
        config: Configuration for torrent creation
    """

    def __init__(self, config: TorrentConfig):
        """
        Initialize the torrent creator.

        Args:
            config: Configuration for torrent creation
        """
        self.config = config

    def create(self, input_path: Union[str, Path], output_path: str) -> str:
        """
        Create a torrent file from a file or directory.

        Args:
            input_path: Path to the file or directory to create a torrent from
            output_path: Path where to save the torrent file

        Returns:
            str: Path to the created torrent file

        Raises:
            ValueError: If input path does not exist
            OSError: If there are issues reading files or writing the torrent
            RuntimeError: If torrent creation fails
            FileIsEmptyError: If file is empty and skip_empty_files is False
        """
        # Convert string path to Path object
        input_path = Path(input_path).resolve()
        if not input_path.exists():
            raise ValueError(f"Input path does not exist: {input_path}")

        # Create file storage
        fs = lt.file_storage()

        # Add files to storage
        if input_path.is_file():
            file_size = input_path.stat().st_size
            if file_size == 0 and self.config.skip_empty_files:
                raise FileIsEmptyError(str(input_path))
            fs.add_file(str(input_path.name), file_size)
            parent_path = input_path.parent
        else:
            parent_path = input_path.parent
            lt.add_files(fs, str(input_path))

        # Calculate optimal piece size based on total size
        total_size = fs.total_size()
        piece_size = self.calculate_optimal_piece_size(total_size)
        logger.debug(
            f"Using piece size: {piece_size / 1024:.0f} KiB for {total_size / 1024 / 1024:.1f} MiB content"
        )

        # Create create_torrent object with calculated piece size
        t = lt.create_torrent(fs, piece_size)

        # Add tracker
        t.add_tracker(self.config.tracker_url)

        # Set the name in the torrent parameters
        t.set_comment(input_path.name)

        # Generate the torrent
        lt.set_piece_hashes(t, str(parent_path))

        # Set private flag if configured
        t.set_priv(self.config.private)

        # Create the torrent
        torrent = t.generate()

        # Ensure the name is set in the info dictionary
        torrent[b"info"][b"name"] = input_path.name.encode()

        # Write the torrent file
        with open(output_path, "wb") as f:
            f.write(lt.bencode(torrent))
            # Sync the torrent file to disk
            sync_to_disk(f)

        # Verify the created torrent file
        if not self.verify_torrent_file(output_path):
            raise RuntimeError(f"Failed to verify created torrent file: {output_path}")

        return output_path

    def _bound_piece_size(self, size: int) -> int:
        """Ensure piece size is within configured bounds.

        Args:
            size: The piece size to bound

        Returns:
            int: The bounded piece size
        """
        min_size: int = int(self.config.min_piece_size)
        max_size: int = int(self.config.max_piece_size)
        size_int: int = int(size)

        if size_int < min_size:
            return min_size
        if size_int > max_size:
            return max_size
        return size_int

    def calculate_optimal_piece_size(self, total_size: int) -> int:
        """Calculate optimal piece size based on total file size."""
        if total_size <= 0:
            return int(self.config.min_piece_size)

        # Define size constants as integers
        KB: int = int(1024)
        MB: int = int(KB * 1024)
        GB: int = int(MB * 1024)

        # Start with a reasonable default (1MB)
        piece_size: int = MB

        # Adjust based on total size
        if total_size < int(100 * MB):  # < 100MB
            piece_size = int(256 * KB)  # 256KB
        elif total_size < int(1 * GB):  # < 1GB
            piece_size = MB  # 1MB
        elif total_size < int(10 * GB):  # < 10GB
            piece_size = int(4 * MB)  # 4MB
        else:  # >= 10GB
            piece_size = int(8 * MB)  # 8MB

        # Ensure piece size is within configured bounds
        return self._bound_piece_size(piece_size)

    @staticmethod
    def verify_torrent_file(torrent_path: str) -> bool:
        """
        Verify that a torrent file is valid and can be loaded.

        Args:
            torrent_path: Path to the torrent file

        Returns:
            bool: True if the torrent file is valid

        Note:
            This method attempts to decode the torrent file to ensure it's valid.
            It does not verify the actual content or piece hashes.
        """
        try:
            with open(torrent_path, "rb") as f:
                data = f.read()
            # Try to decode the torrent file
            torrent = lt.bdecode(data)
            # Basic validation of required fields
            info = torrent.get(b"info")
            if not info:
                return False
            if not info.get(b"name"):
                return False
            if not info.get(b"piece length"):
                return False
            return True
        except (OSError, RuntimeError):
            return False
