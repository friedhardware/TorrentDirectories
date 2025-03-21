"""
Core functionality for creating torrent files with optimal settings.

This module provides the TorrentCreator class for creating torrent files with optimized
piece sizes and settings. It handles both single files and directories, with support
for private torrents, custom trackers, and source tags.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import libtorrent as lt  # type: ignore

from torrent.exceptions import NoDataError, OutputFileExistsError, TorrentCreationError
from torrent.utils.config import TorrentConfig
from torrent.version import __version__

logger = logging.getLogger(__name__)

# Global flag to track interrupt state
interrupted = False


@dataclass
class TorrentVerificationResult:
    """Result of torrent file verification.

    Attributes:
        success: Whether verification was successful
        info_hash: The info hash of the torrent if verification succeeded
        piece_length: The piece length in bytes if verification succeeded
        total_size: The total size in bytes if verification succeeded
        num_pieces: The number of pieces if verification succeeded
        error: Error message if verification failed
    """

    success: bool
    info_hash: Optional[str] = None
    piece_length: Optional[int] = None
    total_size: Optional[int] = None
    num_pieces: Optional[int] = None
    error: Optional[str] = None


class TorrentCreator:
    """Creates torrent files with optimal settings for both single files and directories.

    This class handles the core torrent creation functionality, including:

    * Piece size calculation following strict rules:
        - Must be a power of 2 (e.g. 16 KiB, 32 KiB, 64 KiB)
        - Must be a multiple of 16 KiB
        - Must be between min_piece_size and max_piece_size from config
    * File filtering (hidden files, system files)
    * Torrent verification
    * Empty file handling:
        - Individual empty files (0 bytes) are allowed and included in the torrent
        - However, the total size of all files must be > 0 bytes
        - This is a libtorrent requirement as it needs data to create pieces

    The default configuration uses:

    * Minimum piece size: 256 KiB
    * Maximum piece size: 16 MiB
    * Private flag: True
    * Skip hidden files: True
    * Skip system files: True

    Args:
        config: Configuration object containing torrent creation settings
    """

    def __init__(self, config: TorrentConfig) -> None:
        """Initialize the torrent creator.

        Args:
            config: Configuration object containing torrent creation settings
        """
        self.config = config

    def create(
        self, input_path: Union[str, Path], output_path: Union[str, Path]
    ) -> str:
        """Create a torrent file from a file or directory.

        Args:
            input_path: Path to the input file or directory to create a torrent from
            output_path: Path where the torrent file should be saved

        Returns:
            str: Path to the created torrent file

        Raises:
            TorrentCreationError: If the torrent creation fails for any reason
            OutputFileExistsError: If the output file already exists
            NoDataError: If the total size of all files is 0 bytes. Note that individual
                empty files are allowed, but there must be at least some data overall
                to create pieces from.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise TorrentCreationError(
                message=f"Input path does not exist: {input_path}",
                details={"path": str(input_path)},
            )

        if output_path.exists():
            raise OutputFileExistsError(str(output_path))

        fs = lt.file_storage()
        try:
            lt.add_files(fs, str(input_path))
        except RuntimeError as e:
            if "no files" in str(e):
                # This error means no files were found at all
                raise NoDataError(str(input_path), is_directory=True)
            raise TorrentCreationError(
                message=f"Failed to add files: {e}",
                details={"error": str(e)},
                original_error=e,
            )

        if fs.total_size() == 0:
            # This error means files were found but their total size is 0 bytes
            raise NoDataError(str(input_path), is_directory=input_path.is_dir())

        try:
            # Calculate optimal piece size based on total size
            total_size = fs.total_size()
            piece_size = self.calculate_optimal_piece_size(total_size)
            logger.debug(
                f"Using piece size: {piece_size / 1024:.0f} KiB for {total_size / 1024 / 1024:.1f} MiB content"
            )

            # Create the torrent
            t = lt.create_torrent(fs, piece_size)
            t.set_creator(f"TorrentDirectories v{__version__}")
            t.set_comment(self.config.comment)
            t.set_priv(self.config.private)
            t.add_tracker(self.config.tracker_url)

            # Set piece hashes before generating
            try:
                lt.set_piece_hashes(t, str(input_path.parent))
            except RuntimeError:
                # Check if we were interrupted
                if interrupted:
                    logger.info("Torrent creation interrupted by user")
                    raise TorrentCreationError(
                        message="Torrent creation interrupted by user",
                        details={"path": str(output_path)},
                    )
                raise  # Re-raise if not interrupted

            # Generate torrent file
            torrent = t.generate()

            # Add source as a custom field in the info dictionary
            if self.config.source:
                torrent[b"info"][b"source"] = self.config.source.encode()

            # Save the torrent file
            with open(output_path, "wb") as f:
                f.write(lt.bencode(torrent))

            # Verify the created torrent
            verification_result = self.verify_torrent_file(str(output_path))
            if not verification_result.success:
                # If verification fails, try to clean up and raise an error
                try:
                    os.remove(output_path)
                except OSError:
                    pass  # Ignore cleanup errors
                raise TorrentCreationError(
                    message=f"Failed to verify torrent: {verification_result.error}",
                    details={"verification_error": verification_result.error},
                )

            return str(output_path)

        except Exception as e:
            # Clean up the output file if it exists
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
            except OSError:
                pass  # Ignore cleanup errors
            if isinstance(e, TorrentCreationError):
                raise
            raise TorrentCreationError(
                message=f"Failed to create torrent: {e}",
                details={"error": str(e)},
                original_error=e,
            )

    def _bound_piece_size(self, size: int) -> int:
        """Ensure piece size is within configured bounds.

        Args:
            size: The piece size in bytes to bound

        Returns:
            int: The piece size bounded between min_piece_size and max_piece_size
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
        """Calculate the optimal piece size for a torrent based on its total size.

        The piece size is chosen based on the total size of the torrent:
        * < 50 MB: 256 KB pieces
        * < 150 MB: 1 MB pieces
        * < 1 GB: 1 MB pieces
        * < 10 GB: 4 MB pieces
        * >= 10 GB: 8 MB pieces

        The calculated size is then bounded by min_piece_size and max_piece_size
        from the configuration.

        Args:
            total_size: Total size of the torrent in bytes

        Returns:
            int: Optimal piece size in bytes
        """
        # Constants for piece size calculation
        KB = 1024
        MB = 1024 * KB
        GB = 1024 * MB

        # Calculate piece size based on total size
        if total_size < 50 * MB:  # < 50MB
            piece_size = 256 * KB  # 256KB
        elif total_size < 150 * MB:  # < 150MB
            piece_size = MB  # 1MB
        elif total_size < GB:  # < 1GB
            piece_size = MB  # 1MB
        elif total_size < int(10 * GB):  # < 10GB
            piece_size = int(4 * MB)  # 4MB
        else:  # >= 10GB
            piece_size = int(8 * MB)  # 8MB

        # Ensure piece size is within configured bounds
        return self._bound_piece_size(piece_size)

    @staticmethod
    def verify_torrent_file(torrent_path: str) -> TorrentVerificationResult:
        """Verify that a torrent file is valid and can be loaded.

        This method attempts to load and decode the torrent file, verifying that
        it contains all required fields and can be parsed by libtorrent.

        Args:
            torrent_path: Path to the torrent file to verify

        Returns:
            TorrentVerificationResult: Object containing verification results and metadata.
                If verification succeeds, includes info_hash, piece_length, total_size,
                and num_pieces. If verification fails, includes an error message.
        """
        try:
            with open(torrent_path, "rb") as f:
                data = f.read()
            # Try to decode the torrent file
            torrent = lt.bdecode(data)
            # Basic validation of required fields
            info = torrent.get(b"info")
            if not info:
                return TorrentVerificationResult(
                    success=False, error="Missing info dictionary"
                )

            # Extract metadata
            info_hash = str(lt.torrent_info(torrent).info_hash())
            piece_length = info.get(b"piece length")
            pieces = info.get(b"pieces")
            if not piece_length or not pieces:
                return TorrentVerificationResult(
                    success=False, error="Missing piece information"
                )

            # Calculate total size and number of pieces
            total_size = 0
            if b"files" in info:  # Multi-file mode
                for file_info in info[b"files"]:
                    total_size += file_info[b"length"]
            else:  # Single file mode
                total_size = info[b"length"]

            num_pieces = len(pieces) // 20  # SHA1 hash is 20 bytes

            return TorrentVerificationResult(
                success=True,
                info_hash=info_hash,
                piece_length=piece_length,
                total_size=total_size,
                num_pieces=num_pieces,
            )

        except FileNotFoundError:
            return TorrentVerificationResult(
                success=False, error="No such file or directory"
            )
        except Exception as e:
            return TorrentVerificationResult(success=False, error=str(e))
