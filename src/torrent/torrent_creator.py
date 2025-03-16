"""
Core functionality for creating torrent files with optimal settings.
"""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path
from typing import Optional, Union

import libtorrent  # type: ignore

from .exceptions import (
    CreationError,
    SecurityError,
    TorrentError,
    ValidationError,
)
from .utils.config import TorrentConfig
from .utils.context import secure_temp_environment
from .utils.file_utils import FileNaming, FileSystem, PathSecurity

logger = logging.getLogger(__name__)


class TorrentCreator:
    """
    Creates torrent files with optimal settings for both single files and directories.

    This class handles the core torrent creation functionality, including:
    - Optimal piece size calculation
    - File filtering (hidden files, system files)
    - Progress reporting
    - Torrent verification
    - Path traversal protection
    - Symlink security
    - Temporary file security

    Args:
        tracker_url: URL of the tracker to use
        config: Optional configuration for torrent creation
    """

    def __init__(
        self, tracker_url: str, config: Optional[TorrentConfig] = None
    ) -> None:
        self.tracker_url = tracker_url
        self.config = config or TorrentConfig()
        self._validate_tracker_url()

    def _validate_tracker_url(self) -> None:
        """Validate that the tracker URL is properly formatted."""
        if not self.tracker_url.startswith(("http://", "https://", "udp://")):
            raise ValidationError(f"Invalid tracker URL format: {self.tracker_url}")

    def _validate_paths(
        self,
        input_path: Path,
        output_path: Optional[Path]
    ) -> tuple[Path, Path]:
        """Validate input and output paths.
        
        Args:
            input_path: Path to the input file or directory
            output_path: Optional path for the output torrent file
            
        Returns:
            tuple[Path, Path]: Validated input and output paths
            
        Raises:
            ValidationError: If paths are invalid
            SecurityError: If paths fail security checks
        """
        input_path = input_path.resolve()
        output_path = output_path.resolve() if output_path else Path(f"{input_path.name}.torrent")
        
        # Get the common parent directory for input validation
        parent_input = input_path.parent
        
        # Verify input path safety before checking existence
        if not PathSecurity.is_safe_path(input_path, parent_input):
            raise SecurityError(f"Input path is not safe: {input_path}")
        
        # Ensure input path exists
        if not input_path.exists():
            raise ValidationError(f"Input path does not exist: {input_path}")
        
        # Ensure output directory exists
        output_parent = output_path.parent
        if not output_parent.exists():
            raise ValidationError(f"Output directory does not exist: {output_parent}")
        
        return input_path, output_path

    def _copy_with_sanitized_name(
        self,
        source: Path,
        dest_dir: Path,
        relative_to: Optional[Path] = None,
        preserve_case: bool = True
    ) -> Path:
        """Copy a file with a sanitized name to the destination directory.
        
        Args:
            source: Source file path
            dest_dir: Destination directory
            relative_to: Optional base path for relative path calculation
            preserve_case: Whether to preserve the original case
            
        Returns:
            Path: Path to the copied file
        """
        if relative_to:
            rel_path = source.relative_to(relative_to)
            sanitized_parts = [
                FileNaming.sanitize_filename(p, preserve_case=preserve_case)
                for p in rel_path.parts
            ]
            dest_path = dest_dir.joinpath(*sanitized_parts)
        else:
            sanitized_name = FileNaming.sanitize_filename(
                source.name, preserve_case=preserve_case
            )
            dest_path = dest_dir / sanitized_name
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(source, 'rb') as src, open(dest_path, 'wb') as dst:
            dst.write(src.read())
        return dest_path

    def _create_torrent(
        self,
        fs: libtorrent.file_storage,
        piece_size: int,
        flags: int = libtorrent.create_torrent.v1_only | libtorrent.create_torrent.modification_time
    ) -> libtorrent.create_torrent:
        """Create a torrent with the specified parameters.
        
        Args:
            fs: File storage object
            piece_size: Size of each piece
            flags: Torrent creation flags
            
        Returns:
            libtorrent.create_torrent: Created torrent object
        """
        t = libtorrent.create_torrent(fs, piece_size, flags=flags)
        t.add_tracker(self.tracker_url)
        t.set_creator(f"libtorrent {libtorrent.__version__}")
        t.set_priv(True)  # Set private flag to ensure tracker-only operation
        return t

    def _generate_piece_hashes(
        self,
        torrent: libtorrent.create_torrent,
        temp_dir: Path,
        piece_size: int,
        flags: int
    ) -> None:
        """Generate piece hashes with retry logic for larger piece sizes.
        
        Args:
            torrent: Torrent object
            temp_dir: Directory containing the files
            piece_size: Current piece size
            flags: Torrent creation flags
            
        Raises:
            CreationError: If piece hash generation fails
        """
        try:
            total_pieces = torrent.num_pieces()
            logger.info(f"\nGenerating {total_pieces} pieces...")
            libtorrent.set_piece_hashes(
                torrent,
                str(temp_dir),
                lambda x: logger.debug(f"Generated piece {x}/{total_pieces}"),
            )
            logger.info("Done!")
        except RuntimeError as e:
            if "Operation canceled" in str(e):
                # If piece hash generation fails, try again with a larger piece size
                logger.warning("Piece hash generation failed, retrying with larger piece size")
                new_piece_size = piece_size * 2
                if new_piece_size > self.config.max_piece_size:
                    raise CreationError("Failed to generate piece hashes even with maximum piece size")
                new_torrent = self._create_torrent(torrent.files(), new_piece_size, flags)
                self._generate_piece_hashes(new_torrent, temp_dir, new_piece_size, flags)
            else:
                raise CreationError(f"Failed to generate piece hashes: {e}")

    def calculate_optimal_piece_size(self, total_size: int) -> int:
        """Calculate the optimal piece size for the torrent.
        
        Args:
            total_size: Total size of all files in bytes
            
        Returns:
            int: Optimal piece size in bytes
        """
        # Start with minimum piece size
        piece_size = self.config.min_piece_size
        
        # Calculate number of pieces at current size
        num_pieces = math.ceil(total_size / piece_size)
        
        # If we have a target range, try to hit it
        if self.config.target_pieces:
            min_pieces, max_pieces = self.config.target_pieces
            
            # Increase piece size until we're in range or hit max
            while (
                num_pieces > max_pieces
                and piece_size < self.config.max_piece_size
            ):
                piece_size *= 2
                num_pieces = math.ceil(total_size / piece_size)
            
            # Decrease piece size if we're below minimum pieces
            while (
                num_pieces < min_pieces
                and piece_size > self.config.min_piece_size
            ):
                piece_size //= 2
                num_pieces = math.ceil(total_size / piece_size)
        
        # If no target range, just ensure we don't exceed max pieces
        else:
            while (
                num_pieces > 2000  # Default max pieces
                and piece_size < self.config.max_piece_size
            ):
                piece_size *= 2
                num_pieces = math.ceil(total_size / piece_size)
        
        return piece_size

    def create(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """Create a torrent file from a file or directory.
        
        Args:
            input_path: Path to the file or directory to create a torrent from
            output_path: Optional custom output path for the torrent file
            
        Returns:
            str: Path to the created torrent file
            
        Raises:
            ValidationError: If input validation fails
            SecurityError: If security checks fail
            CreationError: If torrent creation fails
        """
        try:
            # Validate paths
            input_path, output_path = self._validate_paths(
                Path(input_path),
                Path(output_path) if output_path else None
            )
            
            # Create secure temporary environment
            with secure_temp_environment() as (temp_output, temp_dir):
                # Add files and get stats
                fs = libtorrent.file_storage()
                total_files, total_size = self._add_files(fs, input_path, input_path.parent)
                
                if total_files == 0:
                    raise ValidationError(f"No valid files found to add from {input_path}")
                
                logger.info(f"\nTotal: {total_files} files, {total_size/1024/1024:.2f} MiB")
                
                # Calculate piece size and create torrent
                piece_size = self.calculate_optimal_piece_size(total_size)
                logger.info(f"Using piece size: {piece_size/1024/1024:.2f} MiB")
                
                # Create torrent and copy files
                flags = libtorrent.create_torrent.v1_only | libtorrent.create_torrent.modification_time
                t = self._create_torrent(fs, piece_size, flags)
                
                # Copy files with sanitized names
                if input_path.is_file():
                    self._copy_with_sanitized_name(input_path, temp_dir)
                else:
                    for file_path in input_path.rglob("*"):
                        if file_path.is_file() and PathSecurity.is_safe_path(file_path, input_path.parent):
                            self._copy_with_sanitized_name(file_path, temp_dir, input_path.parent)
                
                # Generate piece hashes
                self._generate_piece_hashes(t, temp_dir, piece_size, flags)
                
                # Save and verify torrent file
                torrent_data = libtorrent.bencode(t.generate())
                with open(temp_output, "wb") as torrent_file:
                    torrent_file.write(torrent_data)
                
                if not self.verify_torrent_file(str(temp_output)):
                    raise CreationError("Failed to create a valid torrent file")
                
                # Move to final location
                temp_output.replace(output_path)
                return str(output_path)
                
        except Exception as e:
            # Convert standard exceptions to our custom ones
            if not isinstance(e, TorrentError):
                raise CreationError(f"Failed to create torrent: {e}") from e
            raise

    def _add_files(
        self,
        fs: libtorrent.file_storage,
        input_path: Path,
        base_dir: Path
    ) -> tuple[int, int]:
        """Add files to the torrent.
        
        Args:
            fs: libtorrent file storage object
            input_path: Path to the input file or directory
            base_dir: Base directory for relative path calculation
            
        Returns:
            tuple[int, int]: Number of files added and total size
            
        Raises:
            ValidationError: If no valid files are found
        """
        files_added = 0
        total_size = 0
        logger = logging.getLogger(__name__)
        
        logger.debug(f"Adding files from {input_path} with base_dir {base_dir}")
        
        # Handle single file case
        if input_path.is_file():
            if PathSecurity.is_safe_path(input_path, base_dir):
                # Get relative path components
                rel_path = input_path.relative_to(base_dir)
                sanitized_name = FileNaming.sanitize_filename(
                    str(rel_path),
                    preserve_dots=True,
                    preserve_case=True
                )
                fs.add_file(sanitized_name, input_path.stat().st_size)
                files_added += 1
                total_size = input_path.stat().st_size
        else:
            # Handle directory case
            # Collect all files first and sort them for consistent ordering
            valid_files = []
            
            for root, dirs, files in os.walk(input_path):
                # Skip directories starting with . or ..
                dirs[:] = [d for d in dirs if not (d.startswith(".") or d.startswith(".."))]
                logger.debug(f"Processing directory {root}")
                logger.debug(f"Files in directory: {files}")
                
                for file in files:
                    # Skip files starting with . or ..
                    if file.startswith(".") or file.startswith(".."):
                        logger.debug(f"Skipping file {file} - starts with . or ..")
                        continue
                        
                    file_path = Path(root) / file
                    logger.debug(f"Processing file {file_path}")
                    
                    if PathSecurity.is_safe_path(file_path, base_dir):
                        try:
                            # Get relative path components
                            rel_path = file_path.relative_to(base_dir)
                            logger.debug(f"Relative path: {rel_path}")
                            
                            # Sanitize path
                            sanitized_parts = [
                                FileNaming.sanitize_filename(p, preserve_dots=True, preserve_case=True)
                                for p in rel_path.parts
                            ]
                            sanitized_path = '/'.join(sanitized_parts)
                            logger.debug(f"Sanitized path: {sanitized_path}")
                            valid_files.append((sanitized_path, file_path))
                        except ValueError:
                            # Skip files that can't be made relative to base_dir
                            logger.warning(f"Skipping path {file_path} - cannot make relative to base directory")
                            continue
            
            # Sort files by path for consistent ordering
            valid_files.sort(key=lambda x: x[0])
            logger.debug(f"Valid files: {valid_files}")
            
            # Add files in sorted order
            for sanitized_path, file_path in valid_files:
                if file_path.exists():
                    fs.add_file(sanitized_path, file_path.stat().st_size)
                    files_added += 1
                    total_size += file_path.stat().st_size
                            
        if files_added == 0:
            raise ValidationError("No files added")
            
        return files_added, total_size

    @staticmethod
    def verify_torrent_file(torrent_path: str) -> bool:
        """Verify that a torrent file is valid and can be loaded.
        
        Args:
            torrent_path: Path to the torrent file
            
        Returns:
            bool: True if the torrent file is valid
        """
        try:
            with open(torrent_path, "rb") as f:
                data = f.read()
            # Try to decode the torrent file
            libtorrent.bdecode(data)
            return True
        except (OSError, RuntimeError):
            return False
