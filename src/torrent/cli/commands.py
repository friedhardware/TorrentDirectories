"""
Command handlers for CLI operations.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from ..core import TorrentCreator
from ..manifest import ManifestManager, ManifestError
from ..utils.config import TorrentConfig
from ..utils.file_utils import format_size, get_total_size, list_files

logger = logging.getLogger(__name__)

def process_single(path: str, tracker_url: str, output: Optional[str] = None,
                  config: Optional[TorrentConfig] = None, 
                  dry_run: bool = False,
                  force: bool = False) -> int:
    """
    Create a torrent file from a single file or directory.
    
    Args:
        path: Path to process
        tracker_url: Tracker URL to use
        output: Optional custom output path
        config: Optional torrent configuration
        dry_run: Whether to show what would be done without making changes
        force: Whether to overwrite existing torrent file
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Check if output file exists
        if output and os.path.exists(output) and not force:
            logger.error(f"Output file already exists: {output}")
            logger.error("Use --force to overwrite")
            return 1
            
        creator = TorrentCreator(tracker_url, config)
        
        # Show what would be done in dry run mode
        if dry_run:
            logger.info("\nDry run mode - no changes will be made")
            logger.info(f"Would create torrent from: {path}")
            if output:
                logger.info(f"Would save to: {output}")
            
            # List files that would be included
            files = list_files(path, 
                             skip_hidden=config.skip_hidden if config else True,
                             skip_system=config.skip_system_files if config else True)
            total_size = get_total_size([os.path.join(path, f) for f in files])
            
            logger.info(f"\nWould include {len(files)} files ({format_size(total_size)}):")
            for f in files:
                logger.info(f"  {f}")
            return 0
            
        # Actually create the torrent
        torrent_path = creator.create_torrent(path, output)
        logger.info(f"\nTorrent created successfully: {torrent_path}")
        return 0
        
    except (ValueError, OSError) as e:
        logger.error(f"Error creating torrent: {e}")
        return 1

def process_batch(directory: str, tracker_url: str, clean: bool = False,
                 config: Optional[TorrentConfig] = None,
                 output_dir: Optional[str] = None,
                 dry_run: bool = False,
                 force: bool = False,
                 max_failures: int = 0) -> int:
    """
    Process all subdirectories in a parent directory.
    
    Args:
        directory: Parent directory to process
        tracker_url: Tracker URL to use
        clean: Whether to clean the manifest
        config: Optional torrent configuration
        output_dir: Directory to store torrent files and manifest
        dry_run: Whether to show what would be done without making changes
        force: Whether to overwrite existing torrent files
        max_failures: Maximum allowed failures before stopping
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Create output directory if specified
        if output_dir and not dry_run:
            os.makedirs(output_dir, exist_ok=True)
        
        # Always use manifest.csv in the output directory if specified,
        # otherwise use it in the current directory
        manifest_path = os.path.join(output_dir, 'manifest.csv') if output_dir else 'manifest.csv'
        manifest = ManifestManager(manifest_path)
        creator = TorrentCreator(tracker_url, config)
        
        # Handle manifest cleaning
        if clean:
            missing = manifest.get_missing_torrents()
            if missing:
                logger.warning("\nFound missing torrent files:")
                for path in sorted(missing):
                    logger.warning(f"  {path}")
                    
                if not dry_run:
                    manifest.clean_manifest(directory)
                    logger.info(f"\nRemoved {len(missing)} invalid entries from manifest")
                else:
                    logger.info("\nWould remove invalid entries from manifest")
        
        # Get subdirectories to process
        subdirs = [d for d in os.listdir(directory) 
                  if os.path.isdir(os.path.join(directory, d))]
        
        if not subdirs:
            logger.error(f"No subdirectories found in {directory}")
            return 1
        
        # Show summary in dry run mode
        if dry_run:
            logger.info("\nDry run mode - no changes will be made")
            logger.info(f"\nWould process {len(subdirs)} directories:")
            for subdir in sorted(subdirs):
                full_path = os.path.join(directory, subdir)
                if manifest.is_directory_processed(full_path):
                    logger.info(f"  {subdir}: Would skip (already processed)")
                else:
                    files = list_files(full_path, 
                                     skip_hidden=config.skip_hidden if config else True,
                                     skip_system=config.skip_system_files if config else True)
                    total_size = get_total_size([os.path.join(full_path, f) for f in files])
                    logger.info(f"  {subdir}: Would create torrent ({format_size(total_size)})")
            return 0
        
        # Actually process directories
        logger.info(f"\nProcessing {len(subdirs)} directories:")
        failures = 0
        
        for subdir in sorted(subdirs):
            full_path = os.path.join(directory, subdir)
            
            # Skip if already processed and not forcing
            if manifest.is_directory_processed(full_path) and not force:
                logger.info(f"  {subdir}: Already processed ✓")
                continue
            
            # Create torrent and add to manifest
            try:
                # Set output path in the output directory if specified
                output_path = None
                if output_dir:
                    output_path = os.path.join(output_dir, f"{subdir}.torrent")
                
                torrent_path = creator.create_torrent(full_path, output_path)
                manifest.add_entry(full_path, torrent_path)
                logger.info(f"  {subdir}: Created {torrent_path} ✓")
            except Exception as e:
                logger.error(f"  {subdir}: Failed - {e}")
                failures += 1
                if max_failures > 0 and failures >= max_failures:
                    logger.error(f"\nStopping after {failures} failures")
                    return 1
        
        if failures > 0:
            logger.warning(f"\nCompleted with {failures} failures")
            return 1
            
        return 0
        
    except (ManifestError, ValueError, OSError) as e:
        logger.error(f"Error during batch processing: {e}")
        return 1 