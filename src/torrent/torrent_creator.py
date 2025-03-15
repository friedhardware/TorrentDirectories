"""
Core functionality for creating torrent files with optimal settings.
"""
from __future__ import annotations

import logging
import math
import os
from typing import Optional

import libtorrent # type: ignore

from torrent.utils.config import TorrentConfig

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
        tracker_url: URL of the tracker to use
        config: Optional configuration settings
    """
    
    def __init__(self, tracker_url: str, config: Optional[TorrentConfig] = None):
        self.tracker_url = tracker_url
        self.config = config or TorrentConfig()
        self._validate_tracker_url()
    
    def _validate_tracker_url(self) -> None:
        """Validate that the tracker URL is properly formatted."""
        if not self.tracker_url.startswith(('http://', 'https://', 'udp://')):
            raise ValueError(f"Invalid tracker URL format: {self.tracker_url}")
    
    def create(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Create a torrent file from a file or directory.
        
        Args:
            input_path: Path to the file or directory
            output_path: Optional custom path for the .torrent file
        
        Returns:
            str: Path to the created torrent file
        
        Raises:
            ValueError: If no files were added
            OSError: If there are file system related errors
        """
        input_path = os.path.abspath(input_path)
        if output_path is None:
            output_path = f"{os.path.basename(input_path)}.torrent"
        
        fs = libtorrent.file_storage()
        parent_input = os.path.split(input_path)[0]
        
        total_files = 0
        total_size = 0
        
        # Add files to the torrent
        if os.path.isfile(input_path):
            size = os.path.getsize(input_path)
            fs.add_file(input_path, size)
            total_files = 1
            total_size = size
        else:
            for root, dirs, files in os.walk(input_path):
                # Skip hidden directories if configured
                if self.config.skip_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for f in files:
                    # Skip hidden and system files if configured
                    if self.config.skip_hidden and f.startswith('.'):
                        continue
                    if self.config.skip_system_files and f == 'Thumbs.db':
                        continue
                    
                    fname = os.path.join(root[len(parent_input) + 1:], f)
                    size = os.path.getsize(os.path.join(parent_input, fname))
                    logger.info(f'{size/1024:10.0f} KiB  {fname}')
                    fs.add_file(fname, size)
                    total_files += 1
                    total_size += size
        
        if fs.num_files() == 0:
            raise ValueError(f"No files added from {input_path}")
        
        logger.info(f"\nTotal: {total_files} files, {total_size/1024/1024:.2f} MiB")
        
        # Calculate optimal piece size and create torrent
        optimal_piece_size = self.calculate_optimal_piece_size(fs.total_size())
        logger.info(f'Using piece size: {optimal_piece_size/1024/1024:.2f} MiB')
        
        t = libtorrent.create_torrent(fs, optimal_piece_size)
        t.add_tracker(self.tracker_url)
        t.set_creator('libtorrent %s' % libtorrent.__version__)
        t.set_priv(True)  # Set private flag to ensure tracker-only operation
        
        # Generate pieces with progress indicator
        total_pieces = t.num_pieces()
        logger.info(f"\nGenerating {total_pieces} pieces...")
        libtorrent.set_piece_hashes(t, parent_input, lambda x: logger.debug(f'Generated piece {x}/{total_pieces}'))
        logger.info("Done!")
        
        # Save the torrent file
        with open(output_path, 'wb') as f:
            f.write(libtorrent.bencode(t.generate()))
        
        # Verify the created torrent file
        if not self.verify_torrent_file(output_path):
            os.remove(output_path)
            raise ValueError("Failed to create a valid torrent file")
        
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
        piece_size = 2 ** min_viable_power
        
        # Ensure piece size is within bounds
        piece_size = max(self.config.min_piece_size, 
                        min(piece_size, self.config.max_piece_size))
        
        return piece_size
    
    @staticmethod
    def verify_torrent_file(torrent_path: str) -> bool:
        """
        Verify that a torrent file is valid and can be loaded.
        
        Args:
            torrent_path: Path to the torrent file
        
        Returns:
            bool: True if the torrent file is valid
        """
        try:
            with open(torrent_path, 'rb') as f:
                data = f.read()
            # Try to decode the torrent file
            libtorrent.bdecode(data)
            return True
        except (OSError, RuntimeError):
            return False 