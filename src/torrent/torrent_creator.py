"""
Core functionality for creating torrent files with optimal settings.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Union

import libtorrent  # type: ignore

from torrent.utils.config import TorrentConfig
from torrent.utils.file_utils import sync_to_disk

logger = logging.getLogger(__name__)


class TorrentCreator:
    """
    Creates torrent files with optimal settings for both single files and directories.

    This class handles the core torrent creation functionality, including:
    - Optimal piece size calculation
    - File filtering (hidden files, system files)
    - Progress reporting
    - Torrent verification

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
        """
        # Convert string path to Path object
        input_path = Path(input_path).resolve()
        if not input_path.exists():
            raise ValueError(f"Input path does not exist: {input_path}")

        # Create file storage
        fs = libtorrent.file_storage()
        
        # Add files to storage
        if input_path.is_file():
            fs.add_file(str(input_path.name), input_path.stat().st_size)
            parent_path = input_path.parent
        else:
            parent_path = input_path.parent
            libtorrent.add_files(fs, str(input_path))

        # Calculate optimal piece size based on total size
        total_size = fs.total_size()
        piece_size = self.calculate_optimal_piece_size(total_size)
        logger.debug(f"Using piece size: {piece_size / 1024:.0f} KiB for {total_size / 1024 / 1024:.1f} MiB content")

        # Create create_torrent object with calculated piece size
        t = libtorrent.create_torrent(fs, piece_size)

        # Add tracker
        t.add_tracker(self.config.tracker_url)
        
        # Set the name in the torrent parameters
        t.set_comment(input_path.name)
        
        # Generate the torrent
        libtorrent.set_piece_hashes(t, str(parent_path))
        
        # Set private flag if configured
        t.set_priv(self.config.private)
        
        # Create the torrent
        torrent = t.generate()
        
        # Ensure the name is set in the info dictionary
        torrent[b"info"][b"name"] = input_path.name.encode()
        
        # Write the torrent file
        with open(output_path, "wb") as f:
            f.write(libtorrent.bencode(torrent))
            # Sync the torrent file to disk
            sync_to_disk(f)

        # Verify the created torrent file
        if not self.verify_torrent_file(output_path):
            raise RuntimeError(f"Failed to verify created torrent file: {output_path}")

        return output_path

    def calculate_optimal_piece_size(self, total_size: int) -> int:
        """
        Calculate the optimal piece size for a torrent based on its total size.

        The piece size affects both the torrent file size and client memory usage:
        - Smaller pieces allow more granular downloading but increase torrent file size
        - Larger pieces reduce overhead but require more sequential downloading
        - Aim for 1000-2000 pieces total as a balance for most clients

        Args:
            total_size: Total size of the content in bytes

        Returns:
            int: Optimal piece size in bytes (power of 2 between min and max bounds)
        """
        # Start with minimum piece size that would result in <= max pieces
        min_viable_piece_size = math.ceil(total_size / self.config.target_pieces_max)

        # Round up to nearest power of 2
        min_viable_power = math.ceil(math.log2(min_viable_piece_size))
        piece_size = int(2**min_viable_power)  # Ensure integer result

        # Ensure piece size is within bounds
        piece_size = max(
            self.config.min_piece_size, min(piece_size, self.config.max_piece_size)
        )

        return piece_size

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
            torrent = libtorrent.bdecode(data)
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
