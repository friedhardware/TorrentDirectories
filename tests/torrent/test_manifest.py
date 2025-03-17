"""
Tests for the manifest management system.
"""

from __future__ import annotations

import cProfile
import csv
import io
import os
import pstats
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List

import psutil
import pytest

from torrent.manifest import MANIFEST_FILENAME, ManifestError, ManifestManager


@pytest.fixture
def manifest_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for manifest testing."""
    return tmp_path / "manifest_test"


@pytest.fixture
def manifest_manager(manifest_dir: Path) -> ManifestManager:
    """Create a ManifestManager instance for testing."""
    manifest_dir.mkdir(exist_ok=True)
    return ManifestManager(str(manifest_dir))


@pytest.fixture
def sample_torrent(manifest_dir: Path) -> Path:
    """Create a sample torrent file for testing."""
    manifest_dir.mkdir(exist_ok=True)  # Ensure directory exists
    torrent_file = manifest_dir / "test.torrent"
    torrent_file.write_text("dummy torrent content")
    return torrent_file


def test_manifest_creation(manifest_dir: Path) -> None:
    """Test that manifest file is created with correct headers."""
    ManifestManager(str(manifest_dir))  # Create manager to initialize manifest
    manifest_path = manifest_dir / MANIFEST_FILENAME

    assert manifest_path.exists()
    with open(manifest_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert headers == ["directory_path", "torrent_file", "processed_at"]


def test_is_directory_processed(
    manifest_manager: ManifestManager, manifest_dir: Path, sample_torrent: Path
) -> None:
    """Test checking if a directory has been processed."""
    test_dir = str(manifest_dir / "test_dir")

    # Directory should not be processed initially
    assert not manifest_manager.is_directory_processed(test_dir)

    # Add entry and verify it's marked as processed
    manifest_manager.add_entry(test_dir, str(sample_torrent))
    assert manifest_manager.is_directory_processed(test_dir)


def test_add_entry(
    manifest_manager: ManifestManager, manifest_dir: Path, sample_torrent: Path
) -> None:
    """Test adding entries to the manifest."""
    test_dir = str(manifest_dir / "test_dir")
    manifest_manager.add_entry(test_dir, str(sample_torrent))

    # Verify entry was added correctly
    with open(manifest_manager.manifest_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row["directory_path"] == test_dir
        assert row["torrent_file"] == str(sample_torrent)
        # Verify timestamp format
        datetime.fromisoformat(row["processed_at"])


def test_get_missing_torrents(
    manifest_manager: ManifestManager, manifest_dir: Path
) -> None:
    """Test detection of missing torrent files."""
    test_dir = str(manifest_dir / "test_dir")
    nonexistent_torrent = str(manifest_dir / "nonexistent.torrent")

    # Add entry with non-existent torrent
    manifest_manager.add_entry(test_dir, nonexistent_torrent)

    missing = manifest_manager.get_missing_torrents()
    assert test_dir in missing
    assert len(missing) == 1


def test_clean_manifest(
    manifest_manager: ManifestManager, manifest_dir: Path, sample_torrent: Path
) -> None:
    """Test cleaning the manifest of invalid entries."""
    valid_dir = str(manifest_dir / "valid_dir")
    invalid_dir = str(manifest_dir / "invalid_dir")
    nonexistent_torrent = str(manifest_dir / "nonexistent.torrent")

    # Add both valid and invalid entries
    manifest_manager.add_entry(valid_dir, str(sample_torrent))
    manifest_manager.add_entry(invalid_dir, nonexistent_torrent)

    # Clean manifest
    manifest_manager.clean_manifest(str(manifest_dir))

    # Verify only valid entry remains
    assert manifest_manager.is_directory_processed(valid_dir)
    assert not manifest_manager.is_directory_processed(invalid_dir)


def test_get_processed_directories(
    manifest_manager: ManifestManager, manifest_dir: Path, sample_torrent: Path
) -> None:
    """Test retrieving all processed directories."""
    test_dirs = [str(manifest_dir / f"dir{i}") for i in range(3)]

    # Add multiple entries
    for dir_path in test_dirs:
        manifest_manager.add_entry(dir_path, str(sample_torrent))

    processed = manifest_manager.get_processed_directories()
    assert set(processed) == set(test_dirs)
    assert len(processed) == len(test_dirs)


def test_get_torrent_path(
    manifest_manager: ManifestManager, manifest_dir: Path, sample_torrent: Path
) -> None:
    """Test retrieving torrent path for a processed directory."""
    test_dir = str(manifest_dir / "test_dir")

    # Test non-existent directory
    assert manifest_manager.get_torrent_path(test_dir) is None

    # Add entry and test retrieval
    manifest_manager.add_entry(test_dir, str(sample_torrent))
    assert manifest_manager.get_torrent_path(test_dir) == str(sample_torrent)


def test_manifest_backup_on_clean(
    manifest_manager: ManifestManager, manifest_dir: Path
) -> None:
    """Test that manifest is backed up before cleaning."""
    # Add some entries
    manifest_manager.add_entry(
        str(manifest_dir / "dir1"), str(manifest_dir / "t1.torrent")
    )

    # Clean manifest (should create backup)
    manifest_manager.clean_manifest(str(manifest_dir))

    # Check for backup file
    backup_files = list(manifest_dir.glob("manifest.csv.*"))
    assert len(backup_files) == 1
    assert backup_files[0].name.startswith("manifest.csv.")


def test_unicode_paths(
    manifest_manager: ManifestManager, manifest_dir: Path, sample_torrent: Path
) -> None:
    """Test handling of Unicode paths in manifest."""
    unicode_dir = str(manifest_dir / "测试目录")
    manifest_manager.add_entry(unicode_dir, str(sample_torrent))

    assert manifest_manager.is_directory_processed(unicode_dir)
    assert manifest_manager.get_torrent_path(unicode_dir) == str(sample_torrent)


def test_concurrent_access(
    manifest_manager: ManifestManager, manifest_dir: Path, sample_torrent: Path
) -> None:
    """Test that manifest operations prevent duplicate entries."""
    test_dir = str(manifest_dir / "test_dir")

    # Add entry first time should succeed
    manifest_manager.add_entry(test_dir, str(sample_torrent))

    # Attempting to add the same entry again should raise ManifestError
    with pytest.raises(ManifestError) as exc_info:
        manifest_manager.add_entry(test_dir, str(sample_torrent))
    assert "Directory already exists in manifest" in str(exc_info.value)

    # Verify only one entry exists
    processed = manifest_manager.get_processed_directories()
    assert processed.count(test_dir) == 1


def test_empty_manifest_operations(manifest_manager: ManifestManager) -> None:
    """Test operations on empty manifest."""
    assert not manifest_manager.get_missing_torrents()
    assert not manifest_manager.get_processed_directories()
    assert manifest_manager.get_torrent_path("nonexistent") is None


def test_invalid_manifest_path() -> None:
    """Test handling of invalid manifest directory."""
    with pytest.raises(OSError):
        ManifestManager("/nonexistent/directory")


def test_sync_to_disk_behavior(tmp_path: Path) -> None:
    """Test that writes are immediately synced to disk."""
    manifest_dir = tmp_path / "manifest_test"
    manifest_dir.mkdir()
    manager = ManifestManager(str(manifest_dir))

    # Create a test directory and torrent file
    test_dir = manifest_dir / "test_dir"
    test_dir.mkdir()
    test_torrent = manifest_dir / "test.torrent"
    test_torrent.touch()

    # Add an entry and verify it exists immediately in a new file handle
    manager.add_entry(str(test_dir), str(test_torrent))

    # Open the file with a new handle to verify the write is on disk
    manifest_path = manifest_dir / "manifest.csv"
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert str(test_dir) in content
        assert str(test_torrent) in content


def test_concurrent_manifest_writes(tmp_path: Path) -> None:
    """Test that concurrent writes to the manifest are handled safely."""
    manifest_dir = tmp_path / "manifest_test"
    manifest_dir.mkdir()
    manager = ManifestManager(str(manifest_dir))

    # Create test directories and torrent files
    test_dirs: List[Path] = []
    test_torrents: List[Path] = []
    for i in range(5):
        test_dir = manifest_dir / f"test_dir_{i}"
        test_dir.mkdir()
        test_dirs.append(test_dir)

        test_torrent = manifest_dir / f"test_{i}.torrent"
        test_torrent.touch()
        test_torrents.append(test_torrent)

    # Track successful and failed attempts
    success_count = 0
    error_count = 0

    # Try to add entries concurrently
    def add_entry(idx: int) -> bool:
        try:
            # Use modulo to cycle through the directories, creating more contention
            dir_idx = idx % len(test_dirs)
            manager.add_entry(str(test_dirs[dir_idx]), str(test_torrents[dir_idx]))
            return True
        except ManifestError:
            return False

    # Use ThreadPoolExecutor with more workers and operations to increase contention
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Increase number of concurrent operations
        futures = [executor.submit(add_entry, i) for i in range(50)]
        for future in as_completed(futures):
            if future.result():
                success_count += 1
            else:
                error_count += 1

    # Verify results
    assert success_count > 0, "At least one write should succeed"
    assert error_count > 0, "Some writes should fail due to conflicts"
    assert success_count + error_count == 50, "All operations should complete"
    assert success_count <= 5, "Should not have more successes than unique directories"

    # Verify final manifest state
    processed = manager.get_processed_directories()
    assert (
        len(processed) == success_count
    ), "Number of entries should match successful writes"
    assert len(processed) <= len(
        test_dirs
    ), "Cannot have more entries than unique directories"


def test_manifest_race_condition(tmp_path: Path) -> None:
    """Test that race conditions between manifest operations are detected."""
    manifest_dir = tmp_path / "manifest_test"
    manifest_dir.mkdir()

    # Create two separate manifest managers to simulate different processes
    manager1 = ManifestManager(str(manifest_dir))
    manager2 = ManifestManager(str(manifest_dir))

    # Create test directory and torrent file
    test_dir = manifest_dir / "test_dir"
    test_dir.mkdir()
    test_torrent = manifest_dir / "test.torrent"
    test_torrent.touch()

    # First manager adds the entry
    manager1.add_entry(str(test_dir), str(test_torrent))

    # Second manager tries to add the same entry
    with pytest.raises(ManifestError) as exc_info:
        manager2.add_entry(str(test_dir), str(test_torrent))

    assert "Directory already exists in manifest" in str(exc_info.value)

    # Verify only one entry exists
    processed = manager1.get_processed_directories()
    assert len(processed) == 1


def test_manifest_backup_sync(tmp_path: Path) -> None:
    """Test that manifest backups are properly synced to disk."""
    manifest_dir = tmp_path / "manifest_test"
    manifest_dir.mkdir()
    manager = ManifestManager(str(manifest_dir))

    # Create and add a test entry
    test_dir = manifest_dir / "test_dir"
    test_dir.mkdir()
    test_torrent = manifest_dir / "test.torrent"
    test_torrent.touch()

    manager.add_entry(str(test_dir), str(test_torrent))

    # Clean manifest which creates a backup
    manager.clean_manifest(str(manifest_dir))

    # Find the backup file
    backup_files = [
        f for f in os.listdir(manifest_dir) if f.startswith("manifest.csv.bak_")
    ]
    assert len(backup_files) == 1

    # Verify backup content is immediately readable
    backup_path = manifest_dir / backup_files[0]
    with open(backup_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert str(test_dir) in content
        assert str(test_torrent) in content


def test_cache_behavior(manifest_dir: Path, sample_torrent: Path) -> None:
    """Test cache behavior with different configurations."""
    # Test default cache (enabled)
    manager_default = ManifestManager(str(manifest_dir))
    test_dir = str(manifest_dir / "test_dir")

    # Cache should be empty initially
    assert len(manager_default._cache) == 0

    # Add entry and verify it's cached
    manager_default.add_entry(test_dir, str(sample_torrent))
    assert len(manager_default._cache) == 1
    assert manager_default._cache.get_entry(test_dir) is not None

    # Test disabled cache
    manager_disabled = ManifestManager(str(manifest_dir), use_cache=False)
    assert not manager_disabled._cache.is_enabled()

    # Test size-limited cache
    manager_limited = ManifestManager(str(manifest_dir), cache_size=2)
    for i in range(3):
        dir_path = str(manifest_dir / f"dir{i}")
        manager_limited.add_entry(dir_path, str(sample_torrent))
    assert len(manager_limited._cache) == 2  # Should respect size limit


def test_cache_preloading(tmp_path: Path, sample_torrent: Path) -> None:
    """Test cache preloading behavior."""
    manifest_dir = tmp_path / "manifest_test_preload"  # Changed to unique name
    manifest_dir.mkdir()

    # Create manager and add some entries
    manager = ManifestManager(str(manifest_dir))
    test_dirs = [str(manifest_dir / f"dir{i}") for i in range(3)]
    for dir_path in test_dirs:
        manager.add_entry(dir_path, str(sample_torrent))

    # Create new manager with preloading
    manager_preload = ManifestManager(str(manifest_dir), preload_cache=True)
    assert len(manager_preload._cache) == 3
    for dir_path in test_dirs:
        assert manager_preload._cache.get_entry(dir_path) is not None

    # Create new manager without preloading
    manager_no_preload = ManifestManager(str(manifest_dir), preload_cache=False)
    assert len(manager_no_preload._cache) == 0  # Cache should be empty initially

    # Verify cache loads on first access
    assert manager_no_preload.is_directory_processed(test_dirs[0])
    assert len(manager_no_preload._cache) > 0


def test_manifest_basic_performance(tmp_path: Path) -> None:
    """Test basic performance with a moderate number of entries."""
    manifest = ManifestManager(str(tmp_path))
    process = psutil.Process()
    num_entries = 1_000  # Small enough for regular testing

    # Measure initial metrics
    start_time = time.time()
    start_memory = process.memory_info().rss

    # Add entries
    for i in range(num_entries):
        directory = f"/test/dir_{i}"
        torrent = f"torrent_{i}.torrent"
        manifest.add_entry(directory, torrent)

    # Calculate final metrics
    total_time = time.time() - start_time
    memory_used = (process.memory_info().rss - start_memory) / 1024 / 1024  # MB

    # Basic performance assertions
    assert total_time < 10.0, "Basic operations should complete within 10 seconds"
    assert memory_used < 100.0, "Memory usage should be reasonable"

    # Verify all entries are accessible
    for i in range(num_entries):
        directory = f"/test/dir_{i}"
        assert manifest.is_directory_processed(directory)

