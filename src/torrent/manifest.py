"""
Manifest management for tracking processed directories.
"""

from __future__ import annotations

import csv
import fcntl
import logging
import os
from datetime import datetime
from typing import List, Optional, Set

from .utils.file_utils import backup_file, sync_to_disk
from .utils.manifest_cache import ManifestCache

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "manifest.csv"


class ManifestError(Exception):
    """Base class for manifest-related errors."""

    pass


class ManifestManager:
    """Manages the manifest file for tracking processed directories."""

    def __init__(
        self,
        output_dir: Optional[str] = None,
        use_cache: bool = True,
        cache_size: Optional[int] = None,
        preload_cache: bool = True,
    ):
        """
        Initialize the manifest manager.

        Args:
            output_dir: Directory where manifest file should be stored. If None,
                       uses current directory.
            use_cache: Whether to use in-memory caching (default: True)
            cache_size: Maximum number of entries to cache (None for unlimited)
            preload_cache: Whether to preload all entries into cache at startup (default: True)
        """
        self.output_dir = output_dir or os.getcwd()
        self.manifest_path = os.path.join(self.output_dir, MANIFEST_FILENAME)
        self._cache = ManifestCache(enabled=use_cache, max_size=cache_size)

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Create manifest file if it doesn't exist
        if not os.path.exists(self.manifest_path):
            self._create_manifest()
        elif preload_cache and use_cache:
            # Preload cache if enabled (now default behavior)
            self._cache.preload(self.manifest_path)

    def _create_manifest(self) -> None:
        """Create a new manifest file with headers."""
        with open(self.manifest_path, "w", newline="", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(["directory_path", "torrent_file", "processed_at"])
                sync_to_disk(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def is_directory_processed(self, directory_path: str) -> bool:
        """Check if a directory has already been processed."""
        # Try cache first
        cache_result = self._cache.is_directory_processed(
            directory_path, self.manifest_path
        )
        if cache_result is not None:
            return cache_result

        # Cache miss or disabled, check file
        with open(self.manifest_path, "r", newline="", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["directory_path"] == directory_path:
                        # Update cache if enabled
                        self._cache.add_entry(
                            directory_path, row["torrent_file"], row["processed_at"]
                        )
                        return True
                return False
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def add_entry(
        self, directory_path: str, torrent_file: str, force: bool = False
    ) -> None:
        """
        Add a new entry to the manifest by appending to the file.

        Args:
            directory_path: Path to the processed directory
            torrent_file: Path to the created torrent file
            force: Whether to overwrite an existing entry for this directory
                  Note: With append-only operation, force=True will add duplicate entries

        Raises:
            ManifestError: If the directory is already in the manifest and force is False
        """
        # Open file with exclusive lock to prevent race conditions
        with open(self.manifest_path, "a+", newline="", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                # Check if directory exists
                if not force:
                    # Seek to beginning to read existing entries
                    f.seek(0)
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0] == directory_path:
                            logger.error(
                                f"Attempted to add duplicate entry for directory: {directory_path}"
                            )
                            logger.error(
                                "This could indicate a concurrent process or duplicate operation"
                            )
                            raise ManifestError(
                                f"Directory already exists in manifest: {directory_path}"
                            )

                # Seek to end for appending
                f.seek(0, 2)  # 2 means seek from end
                processed_at = datetime.now().isoformat()
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow([directory_path, torrent_file, processed_at])
                sync_to_disk(f)
                # Update cache
                self._cache.add_entry(directory_path, torrent_file, processed_at)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def get_missing_torrents(self) -> Set[str]:
        """Get a set of directory paths whose torrent files are missing."""
        missing = set()
        with open(self.manifest_path, "r", newline="", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                reader = csv.DictReader(f)
                for row in reader:
                    if not os.path.exists(row["torrent_file"]):
                        missing.add(row["directory_path"])
                return missing
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def clean_manifest(self, output_dir: str) -> None:
        """Clean the manifest by removing entries with missing torrent files."""
        # First create a backup
        backup_file(self.manifest_path)

        # Read existing entries
        valid_entries = []
        with open(self.manifest_path, "r+", newline="", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                reader = csv.DictReader(f)
                for row in reader:
                    if os.path.exists(row["torrent_file"]):
                        valid_entries.append(row)

                # Write back only valid entries
                f.seek(0)
                f.truncate()
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(["directory_path", "torrent_file", "processed_at"])
                for entry in valid_entries:
                    writer.writerow(
                        [
                            entry["directory_path"],
                            entry["torrent_file"],
                            entry["processed_at"],
                        ]
                    )
                sync_to_disk(f)

                # Invalidate cache since we modified the file
                self._cache.invalidate()
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def get_processed_directories(self) -> List[str]:
        """Get a list of all processed directory paths."""
        # Try cache first if it's enabled and has entries
        if self._cache.is_enabled() and len(self._cache) > 0:
            return list(self._cache.get_all_entries().keys())

        # Cache miss or disabled, read from file
        processed_directories = []
        with open(self.manifest_path, "r", newline="", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                reader = csv.DictReader(f)
                for row in reader:
                    processed_directories.append(row["directory_path"])
                return processed_directories
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def get_torrent_path(self, directory_path: str) -> Optional[str]:
        """
        Get the torrent file path for a processed directory.

        Args:
            directory_path: Path to the processed directory

        Returns:
            Path to the torrent file if it exists, None otherwise
        """
        # Try cache first
        entry = self._cache.get_entry(directory_path)
        if entry is not None:
            return entry.torrent_file

        # Cache miss or disabled, check file
        with open(self.manifest_path, "r", newline="", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["directory_path"] == directory_path:
                        # Update cache
                        self._cache.add_entry(
                            directory_path, row["torrent_file"], row["processed_at"]
                        )
                        return row["torrent_file"]
                return None
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
