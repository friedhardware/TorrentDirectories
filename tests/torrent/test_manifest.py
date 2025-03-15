"""Tests for manifest management functionality."""
from __future__ import annotations

import csv
from datetime import datetime
import os
from pathlib import Path

import pytest

from torrent.manifest import ManifestManager, ManifestError
from torrent.utils.config import ManifestConfig

def test_manifest_constants():
    """Test that ManifestManager uses correct constant values."""
    assert ManifestManager.FIELDNAMES == ("directory_path", "torrent_file", "processed_at")
    assert ManifestManager.ENCODING == "utf-8"

def test_manifest_file_creation(tmp_path: Path):
    """Test that manifest file is created with correct headers and encoding."""
    manifest_path = tmp_path / "manifest.csv"
    config = ManifestConfig(filename=str(manifest_path))
    manager = ManifestManager(config)
    
    # Add an entry to create the file
    manager.add_entry("test/dir", "test.torrent")
    
    # Verify file exists and has correct format
    assert manifest_path.exists()
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Check headers
        assert content.startswith('"directory_path","torrent_file","processed_at"')
        # Check that entry was written with full quoting
        assert '"test/dir"' in content
        assert '"test.torrent"' in content

def test_manifest_file_validation(tmp_path: Path):
    """Test that manifest file validation catches invalid headers."""
    manifest_path = tmp_path / "manifest.csv"
    
    # Create manifest with wrong headers
    with open(manifest_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["wrong", "headers"])
    
    config = ManifestConfig(filename=str(manifest_path))
    with pytest.raises(ManifestError, match="Invalid manifest headers"):
        ManifestManager(config)

def test_manifest_backup_creation(tmp_path: Path):
    """Test that backup is created when cleaning manifest."""
    manifest_path = tmp_path / "manifest.csv"
    config = ManifestConfig(filename=str(manifest_path))
    manager = ManifestManager(config)
    
    # Add an entry
    manager.add_entry("test/dir", "test.torrent")
    
    # Clean manifest (should create backup)
    manager.clean_manifest(str(tmp_path))
    
    # Verify backup exists
    backup_path = Path(str(manifest_path) + ".bak")
    assert backup_path.exists()
    
    # Verify backup has original content
    with open(backup_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "test/dir" in content
        assert "test.torrent" in content 