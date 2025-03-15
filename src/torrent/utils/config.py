"""
Configuration classes for torrent creation and manifest management.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TorrentConfig:
    """Configuration for torrent creation."""
    
    min_piece_size: int = 16 * 1024  # 16 KiB
    max_piece_size: int = 16 * 1024 * 1024  # 16 MiB
    target_pieces_min: int = 1000
    target_pieces_max: int = 2000
    skip_hidden: bool = True
    skip_system_files: bool = True


@dataclass
class ManifestConfig:
    """Configuration for manifest management."""
    
    manifest_file: str = "manifest.json"
    max_failures: Optional[int] = None
    force: bool = False
    clean: bool = False
    
    def get_manifest_path(self, parent_dir: str) -> str:
        """Get the full path to the manifest file."""
        return os.path.join(parent_dir, self.manifest_file) 