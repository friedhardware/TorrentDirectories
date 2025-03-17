"""Tests for torrent creation functionality."""

import os
import tempfile
from pathlib import Path

import libtorrent as lt
import pytest

from torrent.torrent_creator import TorrentCreator
from torrent.utils.config import TorrentConfig

TRACKER_URL = "http://example.com/announce"

def test_torrent_private_by_default():
    """Test that created torrent files are private by default."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_dir = Path(temp_dir) / "test_dir"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("test content")

        # Create torrent with default config (private=True)
        output_path = Path(temp_dir) / "output.torrent"
        creator = TorrentCreator(TRACKER_URL, TorrentConfig())
        creator.create(str(test_dir), str(output_path))

        # Read the torrent file and verify it's private
        info = lt.torrent_info(str(output_path))
        assert info.priv(), "Torrent should be private by default"

def test_torrent_private_override():
    """Test that private flag can be overridden to False."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_dir = Path(temp_dir) / "test_dir"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("test content")

        # Create torrent with private=False
        output_path = Path(temp_dir) / "output.torrent"
        config = TorrentConfig(private=False)
        creator = TorrentCreator(TRACKER_URL, config)
        creator.create(str(test_dir), str(output_path))

        # Read the torrent file and verify it's not private
        info = lt.torrent_info(str(output_path))
        assert not info.priv(), "Torrent should not be private when private=False" 