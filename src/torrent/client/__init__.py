"""
Torrent client module for seeding torrents.

This module provides functionality for running a torrent client that can:
1. Seed torrents from a specified directory
2. Monitor a directory for new torrents
3. Run in conjunction with the batch process
"""

from .client import TorrentClient
from .config import ClientConfig

__all__ = ["TorrentClient", "ClientConfig"]
