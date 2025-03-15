"""Tests for manifest management functionality."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from torrent.manifest import ManifestManager, ManifestError

def test_manifest_creation(tmp_path: Path):
    """Test manifest file creation."""
    # Initialize manager with output directory
    manager = ManifestManager(str(tmp_path))
    manifest_path = tmp_path / "manifest.csv"
    
    # Verify manifest file was created
    assert manifest_path.exists()
    
    # Verify headers
    with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert headers == ['directory_path', 'torrent_file', 'processed_at']

def test_manifest_entry_management(tmp_path: Path):
    """Test adding and checking manifest entries."""
    manager = ManifestManager(str(tmp_path))
    
    # Add an entry
    dir_path = str(tmp_path / "test_dir")
    torrent_path = str(tmp_path / "test.torrent")
    
    # Create the torrent file
    Path(torrent_path).write_text("dummy torrent")
    
    manager.add_entry(dir_path, torrent_path)
    
    # Verify entry was added
    assert manager.is_directory_processed(dir_path)
    assert manager.get_torrent_path(dir_path) == torrent_path

def test_manifest_backup_creation(tmp_path: Path):
    """Test that backup is created when cleaning manifest."""
    manager = ManifestManager(str(tmp_path))
    manifest_path = tmp_path / "manifest.csv"
    
    # Add some entries
    dir_path = str(tmp_path / "test_dir")
    torrent_path = str(tmp_path / "test.torrent")
    manager.add_entry(dir_path, torrent_path)
    
    # Clean manifest (should create backup)
    manager.clean_manifest(str(tmp_path))
    
    # Verify backup was created
    backup_files = list(tmp_path.glob("manifest.csv.bak*"))
    assert len(backup_files) == 1

def test_manifest_missing_torrents(tmp_path: Path):
    """Test detection of missing torrent files."""
    manager = ManifestManager(str(tmp_path))
    
    # Add entries for non-existent torrent files
    dir_path1 = str(tmp_path / "dir1")
    dir_path2 = str(tmp_path / "dir2")
    torrent_path1 = str(tmp_path / "t1.torrent")
    torrent_path2 = str(tmp_path / "t2.torrent")
    
    manager.add_entry(dir_path1, torrent_path1)
    manager.add_entry(dir_path2, torrent_path2)
    
    # Create one of the torrent files
    Path(torrent_path1).write_text("dummy torrent")
    
    # Check missing torrents
    missing = manager.get_missing_torrents()
    assert len(missing) == 1
    assert dir_path2 in missing

def test_manifest_cleaning(tmp_path: Path):
    """Test cleaning manifest of invalid entries."""
    manager = ManifestManager(str(tmp_path))
    manifest_path = tmp_path / "manifest.csv"
    
    # Add some entries
    dir_path1 = str(tmp_path / "dir1")
    dir_path2 = str(tmp_path / "dir2")
    torrent_path1 = str(tmp_path / "t1.torrent")
    torrent_path2 = str(tmp_path / "t2.torrent")
    
    manager.add_entry(dir_path1, torrent_path1)
    manager.add_entry(dir_path2, torrent_path2)
    
    # Create one torrent file
    Path(torrent_path1).write_text("dummy torrent")
    
    # Clean manifest
    manager.clean_manifest(str(tmp_path))
    
    # Verify only valid entry remains
    assert manager.is_directory_processed(dir_path1)
    assert not manager.is_directory_processed(dir_path2) 