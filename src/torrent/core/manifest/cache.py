"""
Thread-safe caching implementation for manifest entries.
"""

from __future__ import annotations

import csv
import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from torrent.core.manifest.exceptions import ManifestCacheError

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached manifest entry."""

    torrent_file: str
    processed_at: str
    last_validated: float  # timestamp of last validation


class ManifestCache:
    """Thread-safe cache for manifest entries."""

    def __init__(self, enabled: bool = True, max_size: Optional[int] = None):
        """
        Initialize the manifest cache.

        Args:
            enabled: Whether the cache is active
            max_size: Optional maximum number of entries to cache (None for unlimited)
        """
        self._enabled = enabled
        self._max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lock = threading.RLock()
        self._last_modified = 0.0  # timestamp of last manifest modification

    def is_enabled(self) -> bool:
        """Check if cache is enabled."""
        return self._enabled

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._cache_lock:
            self._cache.clear()
            self._last_modified = 0.0

    def load_from_file(self, manifest_path: str) -> None:
        """
        Load entries from manifest file into cache.

        Args:
            manifest_path: Path to the manifest file

        Raises:
            ManifestCacheError: If there is an error loading or processing the manifest
        """
        if not self._enabled:
            return

        with self._cache_lock:
            self._cache.clear()
            entries = []  # Temporary storage for entries

            try:
                with open(manifest_path, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        entries.append(
                            (
                                row["directory_path"],
                                CacheEntry(
                                    torrent_file=row["torrent_file"],
                                    processed_at=row["processed_at"],
                                    last_validated=datetime.now().timestamp(),
                                ),
                            )
                        )
            except FileNotFoundError:
                # No file to load is not an error
                return
            except Exception as e:
                logger.error(f"Failed to load manifest cache: {e}")
                self._cache.clear()
                raise ManifestCacheError(f"Failed to load manifest cache: {e}")

            try:
                # Only update cache if we successfully read all entries
                for directory_path, entry in entries:
                    self._cache[directory_path] = entry
                self._last_modified = datetime.now().timestamp()
                logger.debug(f"Loaded {len(self._cache)} entries into cache")
            except Exception as e:
                logger.error(f"Failed to process manifest entries: {e}")
                self._cache.clear()
                raise ManifestCacheError(f"Failed to process manifest entries: {e}")

    def is_directory_processed(
        self, directory_path: str, manifest_path: str
    ) -> Optional[bool]:
        """
        Check if a directory is processed using the cache.

        Args:
            directory_path: Path to check
            manifest_path: Path to manifest file (for loading if needed)

        Returns:
            True if processed, False if not, None if cache disabled

        Raises:
            ManifestCacheError: If there is an error loading the manifest
        """
        if not self._enabled:
            return None

        with self._cache_lock:
            # Load cache if empty
            if not self._cache:
                self.load_from_file(manifest_path)

            return directory_path in self._cache

    def add_entry(
        self, directory_path: str, torrent_file: str, processed_at: str
    ) -> None:
        """
        Add or update an entry in the cache.

        Args:
            directory_path: Path to the processed directory
            torrent_file: Path to the torrent file
            processed_at: ISO format timestamp
        """
        if not self._enabled:
            return

        with self._cache_lock:
            # If we have a size limit and we're at it, don't cache more
            if (
                self._max_size
                and len(self._cache) >= self._max_size
                and directory_path not in self._cache
            ):
                return

            self._cache[directory_path] = CacheEntry(
                torrent_file=torrent_file,
                processed_at=processed_at,
                last_validated=datetime.now().timestamp(),
            )

    def remove_entry(self, directory_path: str) -> None:
        """Remove an entry from the cache."""
        if not self._enabled:
            return

        with self._cache_lock:
            self._cache.pop(directory_path, None)

    def get_entry(self, directory_path: str) -> Optional[CacheEntry]:
        """Get cache entry for a directory."""
        if not self._enabled:
            return None

        with self._cache_lock:
            return self._cache.get(directory_path)

    def invalidate(self) -> None:
        """Invalidate the cache, forcing a reload on next access."""
        self.clear()

    def preload(self, manifest_path: str) -> None:
        """
        Preload all entries from the manifest file into the cache.

        Args:
            manifest_path: Path to the manifest file to load

        Raises:
            ManifestCacheError: If there is an error loading the manifest
        """
        self.load_from_file(manifest_path)

    def get_all_entries(self) -> Dict[str, CacheEntry]:
        """Get a copy of all cached entries."""
        with self._cache_lock:
            return self._cache.copy()

    def __len__(self) -> int:
        """Get number of cached entries."""
        with self._cache_lock:
            return len(self._cache)
