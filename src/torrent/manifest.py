"""
Manifest management for tracking processed directories.
"""
from __future__ import annotations

import csv
import logging
import os
from datetime import datetime
from typing import Optional, Set, List

from .utils.file_utils import backup_file

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "manifest.csv"

class ManifestError(Exception):
    """Base class for manifest-related errors."""
    pass

class ManifestManager:
    """Manages the manifest file for tracking processed directories."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the manifest manager.
        
        Args:
            output_dir: Directory where manifest file should be stored. If None,
                       uses current directory.
        """
        self.output_dir = output_dir or os.getcwd()
        self.manifest_path = os.path.join(self.output_dir, MANIFEST_FILENAME)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create manifest file if it doesn't exist
        if not os.path.exists(self.manifest_path):
            self._create_manifest()
    
    def _create_manifest(self) -> None:
        """Create a new manifest file with headers."""
        with open(self.manifest_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(['directory_path', 'torrent_file', 'processed_at'])
    
    def is_directory_processed(self, directory_path: str) -> bool:
        """Check if a directory has already been processed."""
        with open(self.manifest_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['directory_path'] == directory_path:
                    return True
        return False
    
    def add_entry(self, directory_path: str, torrent_file: str) -> None:
        """Add a new entry to the manifest."""
        with open(self.manifest_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow([directory_path, torrent_file, datetime.now().isoformat()])
    
    def get_missing_torrents(self) -> Set[str]:
        """Get a set of directory paths whose torrent files are missing."""
        missing = set()
        with open(self.manifest_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not os.path.exists(row['torrent_file']):
                    missing.add(row['directory_path'])
        return missing
    
    def clean_manifest(self, output_dir: str) -> None:
        """Clean the manifest by removing entries with missing torrent files."""
        # First create a backup
        backup_file(self.manifest_path)
        
        # Read existing entries
        valid_entries = []
        with open(self.manifest_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if os.path.exists(row['torrent_file']):
                    valid_entries.append(row)
        
        # Write back only valid entries
        with open(self.manifest_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(['directory_path', 'torrent_file', 'processed_at'])
            for entry in valid_entries:
                writer.writerow([
                    entry['directory_path'],
                    entry['torrent_file'],
                    entry['processed_at']
                ])
    
    def get_processed_directories(self) -> List[str]:
        """Get a list of all processed directory paths."""
        processed_directories = []
        with open(self.manifest_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_directories.append(row['directory_path'])
        return processed_directories
    
    def get_torrent_path(self, directory_path: str) -> Optional[str]:
        """
        Get the torrent file path for a processed directory.
        
        Args:
            directory_path: Path to the processed directory
            
        Returns:
            Path to the torrent file if it exists, None otherwise
        """
        with open(self.manifest_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['directory_path'] == directory_path:
                    return row['torrent_file']
        return None 