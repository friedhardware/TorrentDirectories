"""
TorrentDirectories - A tool for creating torrent files from directories.

This package provides functionality for creating torrent files with optimal settings,
both for individual files/directories and batch processing of multiple directories.

Key Features:
- Optimal piece size calculation based on content size
- Support for single file/directory and batch processing modes
- Manifest tracking of processed directories
- Configurable file filtering (hidden files, system files)
- Progress reporting and logging
- Command-line interface with rich options

CLI Usage:
    # Create a torrent from a single file or directory
    torrent-directories file path/to/content http://tracker.com/announce

    # Process all subdirectories in a parent directory
    torrent-directories batch path/to/parent http://tracker.com/announce

    # Show help and all available options
    torrent-directories --help

The CLI provides additional options for:
- Custom piece size bounds (--min-piece-size, --max-piece-size)
- Target piece count range (--target-pieces)
- File filtering (--include-hidden, --include-system)
- Dry run mode (--dry-run)
- Logging control (-v, --log-file)
- Batch processing control (--clean, --force, --max-failures)

For programmatic usage, see the TorrentCreator and ManifestManager classes.
"""
from __future__ import annotations

from torrent.torrent_creator import TorrentCreator
from torrent.manifest import ManifestManager, ManifestError
from torrent.cli import main as cli_main

# This is the single source of truth for the package version
__version__ = "0.7.0"
__all__ = ["TorrentCreator", "ManifestManager", "ManifestError", "cli_main"]
