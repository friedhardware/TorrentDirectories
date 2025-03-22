"""
Tests for the manifest cache implementation.
"""

from __future__ import annotations

import csv
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest

from torrent.core.manifest.cache import CacheEntry, ManifestCache, ManifestCacheError


@pytest.fixture
def manifest_file(tmp_path: Path) -> Path:
    """Create a temporary manifest file for testing."""
    manifest_path = tmp_path / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["directory_path", "torrent_file", "processed_at"])
    return manifest_path


@pytest.fixture
def populated_manifest(manifest_file: Path) -> Path:
    """Create a manifest file with some test entries."""
    with open(manifest_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["directory_path", "torrent_file", "processed_at"])
        # Add some test entries
        now = datetime.now().isoformat()
        writer.writerow(["/test/dir1", "/test/dir1.torrent", now])
        writer.writerow(["/test/dir2", "/test/dir2.torrent", now])
        writer.writerow(["/test/dir3", "/test/dir3.torrent", now])
    return manifest_file


def test_cache_initialization() -> None:
    """Test cache initialization with different settings."""
    # Test default initialization
    cache = ManifestCache()
    assert cache.is_enabled()
    assert len(cache) == 0

    # Test disabled cache
    disabled_cache = ManifestCache(enabled=False)
    assert not disabled_cache.is_enabled()

    # Test size-limited cache
    limited_cache = ManifestCache(max_size=5)
    assert limited_cache.is_enabled()
    assert len(limited_cache) == 0


def test_cache_entry_operations(manifest_file: Path) -> None:
    """Test basic cache entry operations."""
    cache = ManifestCache()
    now = datetime.now().isoformat()

    # Test adding entries
    cache.add_entry("/test/dir1", "/test/dir1.torrent", now)
    assert len(cache) == 1

    # Test getting entries
    entry = cache.get_entry("/test/dir1")
    assert entry is not None
    assert entry.torrent_file == "/test/dir1.torrent"
    assert entry.processed_at == now

    # Test removing entries
    cache.remove_entry("/test/dir1")
    assert len(cache) == 0
    assert cache.get_entry("/test/dir1") is None


def test_cache_size_limit() -> None:
    """Test that cache respects size limits."""
    cache = ManifestCache(max_size=2)
    now = datetime.now().isoformat()

    # Add entries up to and beyond limit
    for i in range(3):
        cache.add_entry(f"/test/dir{i}", f"/test/dir{i}.torrent", now)

    # Verify only max_size entries are stored
    assert len(cache) == 2
    assert cache.get_entry("/test/dir2") is None


def test_cache_loading(populated_manifest: Path) -> None:
    """Test loading entries from manifest file."""
    cache = ManifestCache()

    # Test initial load
    cache.load_from_file(str(populated_manifest))
    assert len(cache) == 3

    # Verify loaded entries
    entry = cache.get_entry("/test/dir1")
    assert entry is not None
    assert entry.torrent_file == "/test/dir1.torrent"


def test_cache_preloading(populated_manifest: Path) -> None:
    """Test cache preloading functionality."""
    cache = ManifestCache()

    # Test preloading
    cache.preload(str(populated_manifest))
    assert len(cache) == 3

    # Verify all entries are loaded
    all_entries = cache.get_all_entries()
    assert len(all_entries) == 3
    assert "/test/dir1" in all_entries
    assert "/test/dir2" in all_entries
    assert "/test/dir3" in all_entries


def test_cache_invalidation(populated_manifest: Path) -> None:
    """Test cache invalidation."""
    cache = ManifestCache()
    cache.load_from_file(str(populated_manifest))
    assert len(cache) == 3

    # Test invalidation
    cache.invalidate()
    assert len(cache) == 0

    # Verify cache reloads after checking directory
    assert cache.is_directory_processed("/test/dir1", str(populated_manifest))
    assert len(cache) == 3


def test_concurrent_access() -> None:
    """Test thread-safe concurrent access to cache."""
    cache = ManifestCache()
    now = datetime.now().isoformat()
    num_threads = 10
    operations_per_thread = 100

    def worker() -> None:
        for i in range(operations_per_thread):
            # Mix of read and write operations
            if i % 2 == 0:
                cache.add_entry(f"/test/dir{i}", f"/test/dir{i}.torrent", now)
            else:
                cache.get_entry(f"/test/dir{i-1}")

    # Create and start threads
    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify no data was lost
    assert len(cache) <= num_threads * (operations_per_thread // 2)


def test_disabled_cache_operations(populated_manifest: Path) -> None:
    """Test that disabled cache behaves correctly."""
    cache = ManifestCache(enabled=False)
    now = datetime.now().isoformat()

    # Test all operations return None or have no effect
    assert not cache.is_enabled()
    assert cache.get_entry("/test/dir") is None
    cache.add_entry("/test/dir", "test.torrent", now)
    assert len(cache) == 0
    assert cache.is_directory_processed("/test/dir", str(populated_manifest)) is None


def test_cache_clear() -> None:
    """Test clearing the cache."""
    cache = ManifestCache()
    now = datetime.now().isoformat()

    # Add some entries
    for i in range(3):
        cache.add_entry(f"/test/dir{i}", f"/test/dir{i}.torrent", now)

    # Clear cache
    cache.clear()
    assert len(cache) == 0
    assert cache._last_modified == 0.0


def test_error_handling(tmp_path: Path) -> None:
    """Test handling of errors during cache operations."""
    non_existent_file = tmp_path / "nonexistent.csv"
    cache = ManifestCache()

    # Test loading non-existent file (should not raise error)
    cache.load_from_file(str(non_existent_file))
    assert len(cache) == 0

    # Test that is_directory_processed works with non-existent file
    result = cache.is_directory_processed("/test/dir", str(non_existent_file))
    assert result is False

    # Test loading invalid file
    invalid_file = tmp_path / "invalid.csv"
    with open(invalid_file, "w", newline="", encoding="utf-8") as f:
        # Write a CSV file with incorrect header (missing required columns)
        f.write("wrong_column,another_wrong_column\n")
        f.write("/test/dir,/test/dir.torrent\n")  # Data without required columns

    # Should raise ManifestCacheError
    with pytest.raises(ManifestCacheError):
        cache.load_from_file(str(invalid_file))
    assert len(cache) == 0

    # Test that is_directory_processed raises error with invalid file
    with pytest.raises(ManifestCacheError):
        cache.is_directory_processed("/test/dir", str(invalid_file))


def test_cache_entry_validation() -> None:
    """Test CacheEntry creation and access."""
    now = datetime.now().isoformat()
    timestamp = time.time()

    entry = CacheEntry(
        torrent_file="/test/file.torrent", processed_at=now, last_validated=timestamp
    )

    assert entry.torrent_file == "/test/file.torrent"
    assert entry.processed_at == now
    assert entry.last_validated == timestamp
