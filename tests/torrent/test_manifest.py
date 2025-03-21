"""
Tests for the manifest management system.
"""

from __future__ import annotations

import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Generator

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


@pytest.fixture
def test_dirs(tmp_path: Path) -> Generator[list[Path], None, None]:
    """Create test directories with content."""
    dirs = []
    for i in range(3):
        test_dir = tmp_path / f"test_dir_{i}"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text(f"content {i}")
        dirs.append(test_dir)
    yield dirs


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


def test_manifest_paths_are_absolute(tmp_path: Path) -> None:
    """Test that all directory paths in the manifest are absolute."""
    # Create manifest directory and manager
    manifest_dir = tmp_path / "manifest_test"
    manifest_dir.mkdir()
    manager = ManifestManager(manifest_dir)

    # Create test directories
    test_dirs = []
    for i in range(6):
        test_dir = manifest_dir / f"test_dir_{i}"
        test_dir.mkdir()
        test_dirs.append(test_dir)

    # Create a test torrent file
    test_torrent = manifest_dir / "test.torrent"
    test_torrent.touch()

    # Save original working directory
    original_cwd = os.getcwd()
    try:
        # Change to manifest directory to test relative paths
        os.chdir(str(manifest_dir))

        # Test cases with different path formats
        test_cases = [
            "test_dir_0",  # Simple name
            "./test_dir_1",  # Current directory
            str(test_dirs[2].absolute()),  # Already absolute
            "test_dir_3",  # Another simple name
            "./test_dir_4",  # Another current directory
            "test_dir_5",  # Another simple name
        ]

        # Add entries to manifest
        for path in test_cases:
            manager.add_entry(path, str(test_torrent))

        # Read manifest and verify paths
        with open(
            manifest_dir / "manifest.csv", "r", newline="", encoding="utf-8"
        ) as f:
            reader = csv.DictReader(f)
            for row in reader:
                path = row["directory_path"]
                # Verify path is absolute
                assert os.path.isabs(path), f"Path '{path}' is not absolute"
                # Verify path exists
                assert os.path.exists(path), f"Path '{path}' does not exist"
                # Verify path is under manifest directory
                assert Path(path).is_relative_to(
                    manifest_dir
                ), f"Path '{path}' is not under manifest directory"

    finally:
        # Restore original working directory
        os.chdir(original_cwd)


def test_manifest_cleaning(
    manifest_manager: ManifestManager, test_dirs: list[Path]
) -> None:
    """Test manifest cleaning functionality."""
    # Add entries with missing torrent files
    for i, dir_path in enumerate(test_dirs):
        torrent_path = dir_path.parent / f"test{i}.torrent"
        manifest_manager.add_entry(str(dir_path), str(torrent_path))

    # Create only one torrent file
    (test_dirs[0].parent / "test0.torrent").touch()

    # Get missing torrents
    missing = manifest_manager.get_missing_torrents()
    assert len(missing) == 2

    # Clean manifest
    manifest_manager.clean_manifest()

    # Verify only valid entry remains
    processed_dirs = manifest_manager.get_processed_directories()
    assert len(processed_dirs) == 1
    assert str(test_dirs[0]) in processed_dirs

    # Verify backup was created with timestamp
    manifest_dir = Path(manifest_manager.output_dir)
    backup_files = list(manifest_dir.glob("manifest.csv.bak_*"))
    assert len(backup_files) > 0, "No backup file was created"


def test_manifest_output_dir_update(
    manifest_manager: ManifestManager, test_dirs: list[Path]
) -> None:
    """Test updating torrent paths when cleaning manifest with new output directory."""
    # Add entries
    for i, dir_path in enumerate(test_dirs):
        torrent_path = dir_path.parent / f"test{i}.torrent"
        torrent_path.touch()  # Create torrent files
        manifest_manager.add_entry(str(dir_path), str(torrent_path))

    # Update output directory
    new_output_dir = Path(manifest_manager.output_dir) / "new_output"
    new_output_dir.mkdir()

    # Move torrent files to new directory
    for i in range(len(test_dirs)):
        old_path = test_dirs[0].parent / f"test{i}.torrent"
        new_path = new_output_dir / f"test{i}.torrent"
        old_path.rename(new_path)

    # Clean manifest with new output directory
    manifest_manager.clean_manifest(str(new_output_dir))

    # Verify torrent paths were updated
    for dir_path in test_dirs:
        torrent_path = manifest_manager.get_torrent_path(str(dir_path))
        assert torrent_path is not None
        assert str(new_output_dir) in str(torrent_path)


def test_error_handling(manifest_dir: Path) -> None:
    """Test error handling in manifest operations."""
    manager = ManifestManager(str(manifest_dir))
    manifest_path = manifest_dir / "manifest.csv"

    # Test with invalid manifest file
    manifest_path.write_text("invalid,csv,content\n")
    with pytest.raises(Exception):  # Should handle CSV parsing errors
        manager.get_processed_directories()

    # Test with permission issues
    os.chmod(manifest_path, 0o000)  # Remove all permissions
    try:
        with pytest.raises(Exception):  # Should handle permission errors
            manager.add_entry("/test/dir", "test.torrent")
    finally:
        os.chmod(manifest_path, 0o666)  # Restore permissions


def test_cache_functionality(manifest_dir: Path, test_dirs: list[Path]) -> None:
    """Test cache behavior with different configurations."""
    # Test with cache disabled
    no_cache_manager = ManifestManager(str(manifest_dir), use_cache=False)
    no_cache_manager.add_entry(str(test_dirs[0]), "test1.torrent")
    assert no_cache_manager.is_directory_processed(str(test_dirs[0]))

    # Test with limited cache size
    small_cache_manager = ManifestManager(str(manifest_dir), cache_size=2)
    small_cache_manager.add_entry(
        str(test_dirs[0]), "test1.torrent", force=True
    )  # Update existing entry
    small_cache_manager.add_entry(str(test_dirs[1]), "test2.torrent")
    small_cache_manager.add_entry(
        str(test_dirs[2]), "test3.torrent"
    )  # Should evict oldest entry

    # Test cache preloading
    preload_manager = ManifestManager(str(manifest_dir), preload_cache=True)
    assert preload_manager.is_directory_processed(
        str(test_dirs[0])
    )  # Should be a cache hit


def test_manifest_absolute_paths_add_entry(
    manifest_manager: ManifestManager, manifest_dir: Path
) -> None:
    """Test that add_entry converts relative paths to absolute paths."""
    # Create test files and directories
    test_dir = manifest_dir / "test_dir"
    test_dir.mkdir()
    test_torrent = manifest_dir / "test.torrent"
    test_torrent.touch()

    # Save original working directory
    original_cwd = os.getcwd()
    try:
        # Change to manifest directory
        os.chdir(str(manifest_dir))

        # Test different path formats
        relative_paths = [
            ("./test_dir", "./test.torrent"),
            ("test_dir", "test.torrent"),
            ("./test_dir/", "./test.torrent"),
            (str(test_dir), str(test_torrent)),  # Already absolute
            ("~/test_dir", "~/test.torrent"),  # Home directory expansion
        ]

        for dir_path, torrent_path in relative_paths:
            home_test_dir = None
            home_test_torrent = None

            try:
                # For home directory test, create the necessary files
                if dir_path.startswith("~"):
                    home_test_dir = os.path.expanduser(dir_path)
                    home_test_torrent = os.path.expanduser(torrent_path)
                    os.makedirs(os.path.dirname(home_test_dir), exist_ok=True)
                    os.makedirs(os.path.dirname(home_test_torrent), exist_ok=True)
                    if not os.path.exists(home_test_dir):
                        os.makedirs(home_test_dir)
                    if not os.path.exists(home_test_torrent):
                        Path(home_test_torrent).touch()

                # Add entry with relative paths
                manifest_manager.add_entry(dir_path, torrent_path)

                # Get the stored paths
                stored_torrent = manifest_manager.get_torrent_path(dir_path)
                assert stored_torrent is not None

                # Verify both paths were converted to absolute
                assert os.path.isabs(stored_torrent)
                if dir_path.startswith("~"):
                    expected_torrent = os.path.realpath(
                        os.path.expanduser(torrent_path)
                    )
                    assert stored_torrent == expected_torrent
                else:
                    assert stored_torrent == str(test_torrent.absolute())

                # Clean manifest for next test
                manifest_manager.clean_manifest(str(manifest_dir))

            finally:
                # Clean up home directory test files if they were created
                if home_test_dir and os.path.exists(home_test_dir):
                    os.rmdir(home_test_dir)
                if home_test_torrent and os.path.exists(home_test_torrent):
                    os.remove(home_test_torrent)

    finally:
        os.chdir(original_cwd)


def test_manifest_absolute_paths_batch_operations(
    manifest_manager: ManifestManager, manifest_dir: Path
) -> None:
    """Test that batch operations maintain absolute paths."""
    # Create test structure
    test_dirs = []
    test_torrents = []
    for i in range(3):
        test_dir = manifest_dir / f"test_dir_{i}"
        test_dir.mkdir()
        test_dirs.append(test_dir)

        test_torrent = manifest_dir / f"test_{i}.torrent"
        test_torrent.touch()
        test_torrents.append(test_torrent)

    # Save original working directory
    original_cwd = os.getcwd()
    try:
        # Change to manifest directory
        os.chdir(str(manifest_dir))

        # Add entries using relative paths
        for i in range(3):
            manifest_manager.add_entry(f"./test_dir_{i}", f"./test_{i}.torrent")

        # Test get_processed_directories
        processed_dirs = manifest_manager.get_processed_directories()
        assert all(os.path.isabs(path) for path in processed_dirs)

        # Test get_missing_torrents
        missing = manifest_manager.get_missing_torrents()
        assert all(os.path.isabs(path) for path in missing)

        # Test after cleaning
        manifest_manager.clean_manifest(str(manifest_dir))
        processed_dirs = manifest_manager.get_processed_directories()
        assert all(os.path.isabs(path) for path in processed_dirs)

    finally:
        os.chdir(original_cwd)


def test_manifest_absolute_paths_symlinks(
    manifest_manager: ManifestManager, manifest_dir: Path
) -> None:
    """Test that symlinks are resolved to absolute paths."""
    # Create test structure
    real_dir = manifest_dir / "real_dir"
    real_dir.mkdir()
    symlink_dir = manifest_dir / "symlink_dir"

    real_torrent = manifest_dir / "real.torrent"
    real_torrent.touch()
    symlink_torrent = manifest_dir / "symlink.torrent"

    # Create symlinks
    os.symlink(str(real_dir), str(symlink_dir))
    os.symlink(str(real_torrent), str(symlink_torrent))

    # Add entry using symlink paths
    manifest_manager.add_entry(str(symlink_dir), str(symlink_torrent))

    # Verify paths are absolute and resolved
    stored_torrent = manifest_manager.get_torrent_path(str(symlink_dir))
    assert stored_torrent is not None
    assert os.path.isabs(stored_torrent)
    assert not os.path.islink(stored_torrent)
    assert stored_torrent == str(real_torrent.absolute())
