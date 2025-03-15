from __future__ import annotations

import math
import os
import csv
import time
from datetime import datetime
from typing import Optional, Dict, Set, List, Tuple

# Third-party imports
import libtorrent  # type: ignore

# Constants for piece size calculation
MIN_PIECE_SIZE = 256 * 1024  # 256 KiB
MAX_PIECE_SIZE = 16 * 1024 * 1024  # 16 MiB
TARGET_PIECES_MIN = 1000
TARGET_PIECES_MAX = 2000

def calculate_optimal_piece_size(total_size: int) -> int:
    """
    Calculate the optimal piece size for a torrent based on its total size.
    
    The piece size affects both the torrent file size and client memory usage:
    - Smaller pieces (256 KiB) allow more granular downloading but increase torrent file size
    - Larger pieces (16 MiB) reduce overhead but require more sequential downloading
    - Aim for 1000-2000 pieces total as a balance for most clients
    
    Args:
        total_size: Total size of the torrent in bytes
    
    Returns:
        int: Optimal piece size in bytes (power of 2 between 256 KiB and 16 MiB)
    """
    # Start with minimum piece size that would result in <= 2000 pieces
    min_viable_piece_size = math.ceil(total_size / TARGET_PIECES_MAX)
    
    # Round up to nearest power of 2
    min_viable_power = math.ceil(math.log2(min_viable_piece_size))
    piece_size = 2 ** min_viable_power
    
    # Ensure piece size is within bounds
    piece_size = max(MIN_PIECE_SIZE, min(piece_size, MAX_PIECE_SIZE))
    
    return piece_size

def verify_torrent_file(torrent_path: str) -> bool:
    """
    Verify that a torrent file is valid and can be loaded.
    
    Args:
        torrent_path: Path to the torrent file to verify
        
    Returns:
        bool: True if the torrent file is valid, False otherwise
    """
    try:
        with open(torrent_path, 'rb') as f:
            data = f.read()
        # Try to decode the torrent file
        libtorrent.bdecode(data)
        return True
    except (OSError, RuntimeError):
        return False

def validate_tracker_url(url: str) -> bool:
    """
    Validate that a tracker URL is properly formatted.
    
    Args:
        url: Tracker URL to validate
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    # Basic validation - should be improved based on specific requirements
    return url.startswith(('http://', 'https://', 'udp://'))

def create_torrent(input_path: str, tracker_url: str, output_path: Optional[str] = None) -> str:
    """
    Create a torrent file from a file or directory.
    
    This function handles both single files and directories, automatically
    calculating the optimal piece size based on total content size. It skips
    hidden files/directories and common system files.
    
    Args:
        input_path: Path to the file or directory to create a torrent from
        tracker_url: URL of the tracker to use
        output_path: Optional path for the output .torrent file. If not provided,
                    will use input name with .torrent extension
    
    Returns:
        str: Path to the created torrent file
    
    Raises:
        ValueError: If no files were added or tracker URL is invalid
        OSError: If there are file system related errors
    """
    if not validate_tracker_url(tracker_url):
        raise ValueError(f"Invalid tracker URL format: {tracker_url}")
    
    input_path = os.path.abspath(input_path)
    if output_path is None:
        output_path = f"{os.path.basename(input_path)}.torrent"
    
    fs = libtorrent.file_storage()
    parent_input = os.path.split(input_path)[0]
    
    total_files = 0
    total_size = 0
    
    # Add files to the torrent
    if os.path.isfile(input_path):
        size = os.path.getsize(input_path)
        fs.add_file(input_path, size)
        total_files = 1
        total_size = size
    else:
        for root, dirs, files in os.walk(input_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for f in files:
                # Skip hidden and system files
                if f.startswith('.') or f == 'Thumbs.db':
                    continue
                
                fname = os.path.join(root[len(parent_input) + 1:], f)
                size = os.path.getsize(os.path.join(parent_input, fname))
                print(f'{size/1024:10.0f} KiB  {fname}')
                fs.add_file(fname, size)
                total_files += 1
                total_size += size
    
    if fs.num_files() == 0:
        raise ValueError(f"No files added from {input_path}")
    
    print(f"\nTotal: {total_files} files, {total_size/1024/1024:.2f} MiB")
    
    # Calculate optimal piece size and create torrent
    optimal_piece_size = calculate_optimal_piece_size(fs.total_size())
    print(f'Using piece size: {optimal_piece_size/1024/1024:.2f} MiB')
    
    t = libtorrent.create_torrent(fs, optimal_piece_size)
    t.add_tracker(tracker_url)
    t.set_creator('libtorrent %s' % libtorrent.__version__)
    
    # Generate pieces with progress indicator
    total_pieces = t.num_pieces()
    print(f"\nGenerating {total_pieces} pieces:", end='', flush=True)
    libtorrent.set_piece_hashes(t, parent_input, lambda x: print('.', end='', flush=True))
    print(" Done!")
    
    # Save the torrent file
    with open(output_path, 'wb') as f:
        f.write(libtorrent.bencode(t.generate()))
    
    # Verify the created torrent file
    if not verify_torrent_file(output_path):
        os.remove(output_path)
        raise ValueError("Failed to create a valid torrent file")
    
    return output_path

def clean_manifest(output_dir: str, manifest: Dict[str, tuple[str, datetime]]) -> Dict[str, tuple[str, datetime]]:
    """
    Clean the manifest by removing entries for torrent files that don't exist.
    Creates a new manifest file with only valid entries.
    
    Args:
        output_dir: Directory containing torrent files and manifest
        manifest: The current manifest data mapping directory paths to (torrent_file, timestamp)
        
    Returns:
        Dict[str, tuple[str, datetime]]: Updated manifest with only valid entries
        
    Note:
        This function will write the cleaned manifest back to disk immediately.
        The manifest file uses CSV format with UTF-8 encoding and full quoting
        to handle special characters in paths.
    """
    # Get set of existing torrent files
    existing_torrents = {f for f in os.listdir(output_dir) if f.endswith('.torrent')}
    
    # Create new manifest with only valid entries
    cleaned_manifest = {
        dir_path: (torrent_file, timestamp)
        for dir_path, (torrent_file, timestamp) in manifest.items()
        if torrent_file in existing_torrents
    }
    
    # Write the cleaned manifest
    manifest_path = os.path.join(output_dir, "manifest.csv")
    with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["directory_path", "torrent_file", "processed_at"])
        for dir_path, (torrent_file, timestamp) in cleaned_manifest.items():
            writer.writerow([dir_path, torrent_file, timestamp.isoformat(timespec='seconds')])
    
    return cleaned_manifest

def validate_manifest_state(output_dir: str, manifest: Dict[str, tuple[str, datetime]]) -> tuple[bool, Dict[str, tuple[str, datetime]]]:
    """
    Validate the state between manifest and output directory.
    Returns True if state is valid or user confirms to proceed.
    
    This function performs thorough validation:
    1. Checks if manifest entries point to existing torrent files
    2. Checks if all torrent files in output_dir are in the manifest
    3. Reports any discrepancies and asks for user confirmation
    
    The function will automatically clean up inconsistencies if the user confirms:
    - Remove manifest entries for missing torrent files
    - Remove untracked torrent files from disk
    
    Args:
        output_dir: Directory containing torrent files and manifest
        manifest: The loaded manifest data
        
    Returns:
        tuple[bool, Dict[str, tuple[str, datetime]]]: 
            - bool: True if processing should continue, False if it should abort
            - Dict: The manifest (cleaned if user confirmed, original otherwise)
    """
    # Get list of actual torrent files in the directory
    existing_torrents = {f for f in os.listdir(output_dir) if f.endswith('.torrent')}
    
    # Get set of torrent files mentioned in manifest
    manifest_torrents = {torrent_file for _, (torrent_file, _) in manifest.items()}
    
    # Case 1: No manifest and no torrent files - valid first run
    if not manifest and not existing_torrents:
        return True, manifest
    
    # Find discrepancies
    missing_from_disk = manifest_torrents - existing_torrents
    missing_from_manifest = existing_torrents - manifest_torrents
    
    # Case 2: Everything matches - valid state
    if not missing_from_disk and not missing_from_manifest:
        return True, manifest
    
    # Case 3: Discrepancies found - warn user and ask for confirmation
    print("\nWARNING: Found discrepancies between manifest and torrent files:")
    
    if missing_from_disk:
        print("\nTorrent files listed in manifest but missing from disk:")
        for torrent in sorted(missing_from_disk):
            # Find the directory this torrent was for
            for dir_path, (tf, ts) in manifest.items():
                if tf == torrent:
                    print(f"  {torrent} (for directory: {dir_path}, processed at: {ts.isoformat(timespec='seconds')})")
    
    if missing_from_manifest:
        print("\nTorrent files found but not listed in manifest:")
        for torrent in sorted(missing_from_manifest):
            print(f"  {torrent}")
    
    print("\nThis could mean:")
    print("- Torrent files were manually moved or deleted")
    print("- The manifest file is out of sync")
    print("- There was an interruption during previous processing")
    
    print("\nThe following actions will be taken:")
    if missing_from_disk:
        print(f"- Remove {len(missing_from_disk)} invalid entries from manifest")
    if missing_from_manifest:
        print(f"- Remove {len(missing_from_manifest)} untracked torrent files")
    
    response = input("\nDo you want to proceed with cleaning up these discrepancies? (y/N): ").lower()
    if response == 'y':
        # First clean the manifest of missing files
        cleaned_manifest = clean_manifest(output_dir, manifest)
        print(f"\nRemoved {len(missing_from_disk)} invalid entries from manifest")
        
        # Then handle untracked torrent files
        if missing_from_manifest:
            # Remove all untracked torrents
            for torrent in missing_from_manifest:
                try:
                    os.remove(os.path.join(output_dir, torrent))
                    print(f"Removed untracked torrent: {torrent}")
                except OSError as e:
                    print(f"Warning: Failed to remove {torrent}: {e}")
        
        return True, cleaned_manifest
    
    # User cancelled
    return False, manifest

def load_manifest(output_dir: str) -> Dict[str, tuple[str, datetime]]:
    """
    Load the manifest file from the output directory.
    
    The manifest is a CSV file that tracks processed directories and their
    corresponding torrent files. Each entry contains:
    - Absolute path to the processed directory
    - Name of the created torrent file
    - Timestamp when the torrent was created (ISO format)
    
    Args:
        output_dir: Directory containing the manifest file
        
    Returns:
        Dict[str, tuple[str, datetime]]: Dictionary mapping absolute directory paths 
        to (torrent_file, timestamp) tuples
        
    Note:
        - Invalid rows in the manifest are skipped with a warning
        - Missing manifest file returns an empty dictionary
        - File access errors are logged as warnings
    """
    manifest_path = os.path.join(output_dir, "manifest.csv")
    manifest: Dict[str, tuple[str, datetime]] = {}
    
    try:
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f, quoting=csv.QUOTE_ALL)
                header = next(reader, None)
                if header != ["directory_path", "torrent_file", "processed_at"]:
                    print("Warning: Manifest file has invalid header, treating as empty")
                    return manifest
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        if len(row) == 3:  # directory_path, torrent_file, timestamp
                            directory_path, torrent_file, timestamp_str = row
                            # Parse ISO timestamp directly to datetime
                            timestamp = datetime.fromisoformat(timestamp_str)
                            manifest[directory_path] = (torrent_file, timestamp)
                        else:
                            print(f"Warning: Invalid manifest entry on line {row_num}, skipping")
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Failed to parse manifest entry on line {row_num}: {e}")
                        continue
    except OSError as e:
        print(f"Warning: Failed to load manifest file: {e}")
    
    return manifest

def append_to_manifest(output_dir: str, directory_path: str, torrent_file: str, timestamp: datetime) -> None:
    """
    Append a new entry to the manifest file.
    
    This function uses append mode to ensure atomic writes and prevent data loss
    during interruptions. It handles creating the manifest file with proper headers
    if it doesn't exist.
    
    Args:
        output_dir: Directory containing the manifest file
        directory_path: Absolute path to the processed directory
        torrent_file: Name of the created torrent file
        timestamp: Processing timestamp (as datetime object)
        
    Note:
        - Uses CSV format with full quoting to handle special characters
        - Timestamps are stored in ISO format for human readability
        - File access errors are logged as warnings
    """
    manifest_path = os.path.join(output_dir, "manifest.csv")
    try:
        # Create file with header if it doesn't exist
        if not os.path.exists(manifest_path):
            with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(["directory_path", "torrent_file", "processed_at"])
        
        # Format datetime to ISO format
        timestamp_str = timestamp.isoformat(timespec='seconds')
        
        # Append new entry
        with open(manifest_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow([directory_path, torrent_file, timestamp_str])
    except OSError as e:
        print(f"Warning: Failed to update manifest file: {e}")

def create_directory_torrents(parent_dir: str, tracker_url: str, output_dir: Optional[str] = None) -> list[str]:
    """
    Create torrent files for each subdirectory in the specified directory.
    
    This function processes a parent directory in batch mode, creating separate
    torrent files for each of its immediate subdirectories. It maintains a manifest
    file to track processed directories, allowing for safe interruption and resume.
    
    Features:
    - Skips hidden directories (those starting with a dot)
    - Maintains a manifest of processed directories
    - Validates existing torrent files against manifest
    - Handles interruptions gracefully
    - Reports progress and statistics
    
    The manifest file (manifest.csv) contains:
    - Absolute paths to processed directories
    - Names of created torrent files
    - Timestamps of when each torrent was created
    
    Args:
        parent_dir: Path to the directory containing subdirectories to process
        tracker_url: URL of the tracker to use
        output_dir: Directory to save the torrent files in. If not provided,
                   defaults to "[parent_dir_name]_torrents"
    
    Returns:
        list[str]: List of paths to the newly created torrent files
    
    Raises:
        ValueError: If no valid subdirectories are found or tracker URL is invalid
        OSError: If there are file system related errors
    """
    if not validate_tracker_url(tracker_url):
        raise ValueError(f"Invalid tracker URL format: {tracker_url}")
    
    parent_dir = os.path.abspath(parent_dir)
    if not os.path.isdir(parent_dir):
        raise ValueError(f"{parent_dir} is not a directory")
    
    # Create output directory name based on parent directory if not provided
    if output_dir is None:
        parent_name = os.path.basename(parent_dir)
        output_dir = f"{parent_name}_torrents"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load existing manifest
    manifest = load_manifest(output_dir)
    
    # Validate manifest state and get user confirmation if needed
    should_continue, manifest = validate_manifest_state(output_dir, manifest)
    if not should_continue:
        print("Operation cancelled by user")
        return []
    
    # Get list of subdirectories
    subdirs = [
        d for d in os.scandir(parent_dir)
        if d.is_dir() and not d.name.startswith('.')
    ]
    
    if not subdirs:
        raise ValueError(f"No subdirectories found in {parent_dir}")
    
    total_dirs = len(subdirs)
    new_dirs = sum(1 for d in subdirs if os.path.abspath(d.path) not in manifest)
    skipped_dirs = total_dirs - new_dirs
    
    print(f"\nFound {total_dirs} directories ({new_dirs} new, {skipped_dirs} already processed)")
    created_torrents = []
    
    # Process each subdirectory
    for i, subdir in enumerate(sorted(subdirs, key=lambda d: d.name), 1):
        subdir_path = os.path.abspath(subdir.path)
        # Skip if already processed
        if subdir_path in manifest:
            torrent_file, timestamp = manifest[subdir_path]
            print(f"\nSkipping [{i}/{total_dirs}]: {subdir.name}")
            print(f"  Already processed: {torrent_file}")
            print(f"  Created at: {timestamp.isoformat(timespec='seconds')}")
            continue
            
        print(f"\nProcessing [{i}/{total_dirs}]: {subdir.name}")
        print("=" * (13 + len(str(total_dirs)) + len(subdir.name)))
        
        output_path = os.path.join(output_dir, f"{subdir.name}.torrent")
        try:
            torrent_path = create_torrent(subdir_path, tracker_url, output_path)
            created_torrents.append(torrent_path)
            # Append new entry to manifest immediately after successful creation
            append_to_manifest(output_dir, subdir_path, os.path.basename(torrent_path), datetime.now())
            print(f"Created torrent: {output_path}")
        except Exception as e:
            print(f"Error creating torrent for {subdir.name}:")
            print(f"  {str(e)}")
            print("Continuing with next directory...")
    
    if created_torrents:
        print(f"\nSuccess! Created {len(created_torrents)} new torrent files in {output_dir}/")
    else:
        print("\nNo new torrent files were created")
    print(f"Total processed: {len(manifest)} directories")
    
    return created_torrents 