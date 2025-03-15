"""
Manifest file management and validation for tracking processed directories.
"""
from __future__ import annotations

import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from torrent.utils.config import ManifestConfig

logger = logging.getLogger(__name__)

class ManifestError(Exception):
    """Base exception for manifest-related errors."""
    pass

class ManifestManager:
    """
    Manages the manifest file for tracking processed directories and their torrent files.
    
    The manifest is a CSV file that records:
    - Directory paths that have been processed
    - Generated torrent file paths
    - Timestamps of when processing occurred
    
    Features:
    - Append-only writes for safety
    - Immediate entry recording after successful torrent creation
    - Header validation on file load
    - Backup creation before modifications
    """
    
    # Constants for manifest file handling
    FIELDNAMES = ("directory_path", "torrent_file", "processed_at")
    ENCODING = "utf-8"
    
    def __init__(self, config: Optional[ManifestConfig] = None):
        """
        Initialize the manifest manager.
        
        Args:
            config: Configuration settings for the manifest file. If None, uses defaults.
        """
        self.config = config or ManifestConfig()
        self._entries: Dict[str, Tuple[str, datetime]] = {}
        self._load_manifest()
    
    def _load_manifest(self) -> None:
        """Load and validate the manifest file if it exists."""
        if not os.path.exists(self.config.filename):
            logger.info(f"No manifest file found at {self.config.filename}")
            return
            
        try:
            with open(self.config.filename, 'r', encoding=self.ENCODING) as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != list(self.FIELDNAMES):
                    raise ManifestError(f"Invalid manifest headers: {reader.fieldnames}")
                    
                for row in reader:
                    dir_path = row['directory_path']
                    torrent_file = row['torrent_file']
                    processed_at = datetime.fromisoformat(row['processed_at'])
                    self._entries[dir_path] = (torrent_file, processed_at)
                    
        except (csv.Error, ValueError) as e:
            raise ManifestError(f"Error reading manifest: {e}")
    
    def add_entry(self, directory_path: str, torrent_file: str) -> None:
        """
        Add a new entry to the manifest.
        
        Args:
            directory_path: Path to the processed directory
            torrent_file: Path to the generated torrent file
        """
        now = datetime.now().isoformat()
        
        # Append the new entry to the manifest file
        with open(self.config.filename, 'a', encoding=self.ENCODING, newline='') as f:
            writer = csv.DictWriter(f, 
                                  fieldnames=self.FIELDNAMES,
                                  quoting=csv.QUOTE_ALL)
            
            # Write headers if this is a new file
            if f.tell() == 0:
                writer.writeheader()
                
            writer.writerow({
                'directory_path': directory_path,
                'torrent_file': torrent_file,
                'processed_at': now
            })
        
        # Update in-memory entries
        self._entries[directory_path] = (torrent_file, datetime.fromisoformat(now))
    
    def get_missing_torrents(self) -> Set[str]:
        """
        Find torrent files listed in the manifest that don't exist on disk.
        
        Returns:
            Set of paths to missing torrent files
        """
        missing = set()
        for dir_path, (torrent_file, _) in self._entries.items():
            if not os.path.exists(torrent_file):
                missing.add(torrent_file)
        return missing
    
    def clean_manifest(self, output_dir: str) -> None:
        """
        Create a new manifest containing only entries with existing torrent files.
        
        Args:
            output_dir: Directory containing torrent files
        """
        # Create backup of current manifest
        if os.path.exists(self.config.filename):
            backup_path = f"{self.config.filename}.bak"
            os.rename(self.config.filename, backup_path)
            logger.info(f"Created manifest backup at {backup_path}")
        
        # Write new manifest with only valid entries
        with open(self.config.filename, 'w', encoding=self.ENCODING, newline='') as f:
            writer = csv.DictWriter(f, 
                                  fieldnames=self.FIELDNAMES,
                                  quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            for dir_path, (torrent_file, processed_at) in self._entries.items():
                if os.path.exists(torrent_file):
                    writer.writerow({
                        'directory_path': dir_path,
                        'torrent_file': torrent_file,
                        'processed_at': processed_at.isoformat()
                    })
    
    def is_directory_processed(self, directory_path: str) -> bool:
        """
        Check if a directory has already been processed.
        
        Args:
            directory_path: Path to check
            
        Returns:
            True if the directory is in the manifest and its torrent exists
        """
        if directory_path not in self._entries:
            return False
            
        torrent_file, _ = self._entries[directory_path]
        return os.path.exists(torrent_file)
    
    def get_processed_directories(self) -> List[str]:
        """Get a list of all processed directory paths."""
        return list(self._entries.keys())
    
    def get_torrent_path(self, directory_path: str) -> Optional[str]:
        """
        Get the torrent file path for a processed directory.
        
        Args:
            directory_path: Path to the processed directory
            
        Returns:
            Path to the torrent file if it exists, None otherwise
        """
        if directory_path in self._entries:
            torrent_file, _ = self._entries[directory_path]
            if os.path.exists(torrent_file):
                return torrent_file
        return None 