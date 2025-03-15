import math
import os
import csv
import time
from datetime import datetime
import libtorrent # type: ignore
from typing import Optional, Dict

def calculate_optimal_piece_size(total_size):
    """
    Calculate the optimal piece size for a torrent based on its total size.
    
    Guidelines:
    - Minimum piece size: 256 KiB
    - Maximum piece size: 16 MiB
    - Target number of pieces: Between 1000 and 2000 for optimal balance
    - Piece size must be a power of 2
    
    Args:
        total_size (int): Total size of the torrent in bytes
    
    Returns:
        int: Optimal piece size in bytes
    """
    MIN_PIECE_SIZE = 256 * 1024  # 256 KiB
    MAX_PIECE_SIZE = 16 * 1024 * 1024  # 16 MiB
    TARGET_PIECES_MIN = 1000
    TARGET_PIECES_MAX = 2000
    
    # Start with minimum piece size that would result in <= 2000 pieces
    min_viable_piece_size = math.ceil(total_size / TARGET_PIECES_MAX)
    
    # Round up to nearest power of 2
    min_viable_power = math.ceil(math.log2(min_viable_piece_size))
    piece_size = 2 ** min_viable_power
    
    # Ensure piece size is within bounds
    piece_size = max(MIN_PIECE_SIZE, min(piece_size, MAX_PIECE_SIZE))
    
    return piece_size

def create_torrent(input_path: str, tracker_url: str, output_path: Optional[str] = None) -> str:
    """
    Create a torrent file from a file or directory.
    
    Args:
        input_path: Path to the file or directory to create a torrent from
        tracker_url: URL of the tracker to use
        output_path: Optional path for the output .torrent file. If not provided,
                    will use input name with .torrent extension
    
    Returns:
        str: Path to the created torrent file
    
    Raises:
        ValueError: If no files were added to the torrent
        OSError: If there are file system related errors
    """
    input_path = os.path.abspath(input_path)
    if output_path is None:
        output_path = f"{os.path.basename(input_path)}.torrent"
    
    fs = libtorrent.file_storage()
    parent_input = os.path.split(input_path)[0]
    
    # Add files to the torrent
    if os.path.isfile(input_path):
        size = os.path.getsize(input_path)
        fs.add_file(input_path, size)
    else:
        for root, dirs, files in os.walk(input_path):
            # skip directories starting with .
            if os.path.split(root)[1][0] == '.':
                continue

            for f in files:
                # skip files starting with .
                if f[0] == '.':
                    continue

                # skip thumbs.db on windows
                if f == 'Thumbs.db':
                    continue

                fname = os.path.join(root[len(parent_input) + 1:], f)
                size = os.path.getsize(os.path.join(parent_input, fname))
                print('%10d kiB  %s' % (size / 1024, fname))
                fs.add_file(fname, size)
    
    if fs.num_files() == 0:
        raise ValueError(f"No files added from {input_path}")
    
    # Calculate optimal piece size and create torrent
    optimal_piece_size = calculate_optimal_piece_size(fs.total_size())
    print(f'Using piece size: {optimal_piece_size / 1024 / 1024:.2f} MiB')
    
    t = libtorrent.create_torrent(fs, optimal_piece_size)
    t.add_tracker(tracker_url)
    t.set_creator('libtorrent %s' % libtorrent.__version__)
    
    # Generate pieces
    libtorrent.set_piece_hashes(t, parent_input, lambda x: print('.', end='', flush=True))
    print()  # New line after progress dots
    
    # Save the torrent file
    with open(output_path, 'wb') as f:
        f.write(libtorrent.bencode(t.generate()))
    
    return output_path

def clean_manifest(output_dir: str, manifest: Dict[str, tuple[str, datetime]]) -> Dict[str, tuple[str, datetime]]:
    """
    Clean the manifest by removing entries for torrent files that don't exist.
    Creates a new manifest file with only valid entries.
    
    Args:
        output_dir: Directory containing torrent files and manifest
        manifest: The current manifest data
        
    Returns:
        Dict[str, tuple[str, datetime]]: Updated manifest with only valid entries
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
        print("- Add any valid torrent files to manifest (if source directories exist)")
    
    response = input("\nDo you want to proceed with cleaning up these discrepancies? (y/N): ").lower()
    if response == 'y':
        # First clean the manifest of missing files
        cleaned_manifest = clean_manifest(output_dir, manifest)
        print(f"\nRemoved {len(missing_from_disk)} invalid entries from manifest")
        
        # Then handle untracked torrent files
        if missing_from_manifest:
            # First remove all untracked torrents
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
    
    Args:
        output_dir: Directory containing the manifest file
        
    Returns:
        Dict[str, tuple[str, datetime]]: Dictionary mapping absolute directory paths to (torrent_file, timestamp) tuples
    """
    manifest_path = os.path.join(output_dir, "manifest.csv")
    manifest = {}
    
    try:
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f, quoting=csv.QUOTE_ALL)
                next(reader, None)  # Skip header row
                for row in reader:
                    try:
                        if len(row) == 3:  # directory_path, torrent_file, timestamp
                            directory_path, torrent_file, timestamp_str = row
                            # Parse ISO timestamp directly to datetime
                            timestamp = datetime.fromisoformat(timestamp_str)
                            manifest[directory_path] = (torrent_file, timestamp)
                    except (ValueError, IndexError):
                        continue  # Skip invalid rows
    except OSError as e:
        print(f"Warning: Failed to load manifest file: {e}")
    
    return manifest

def append_to_manifest(output_dir: str, directory_path: str, torrent_file: str, timestamp: datetime) -> None:
    """
    Append a new entry to the manifest file.
    
    Args:
        output_dir: Directory containing the manifest file
        directory_path: Absolute path to the processed directory
        torrent_file: Name of the created torrent file
        timestamp: Processing timestamp (as datetime object)
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
        
        with open(manifest_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow([directory_path, torrent_file, timestamp_str])
    except OSError as e:
        print(f"Warning: Failed to update manifest file: {e}")

def create_directory_torrents(parent_dir: str, tracker_url: str, output_dir: Optional[str] = None) -> list[str]:
    """
    Create torrent files for each subdirectory in the specified directory.
    
    This function walks through a parent directory and creates a separate torrent
    file for each of its subdirectories. It skips hidden directories (those starting
    with a dot) and handles errors for individual subdirectories gracefully.
    
    The function maintains a manifest file in the output directory to track which
    subdirectories have been processed. This allows for resuming interrupted batch
    operations by skipping already processed directories.
    
    Args:
        parent_dir: Path to the directory containing subdirectories to process
        tracker_url: URL of the tracker to use
        output_dir: Directory to save the torrent files in. If not provided,
                   defaults to "[parent_dir_name]_torrents"
    
    Returns:
        list[str]: List of paths to the created torrent files
    
    Raises:
        ValueError: If no valid subdirectories are found
        OSError: If there are file system related errors
    """
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
    
    print(f"Found {total_dirs} directories ({new_dirs} new, {skipped_dirs} already processed)")
    created_torrents = []
    
    # Process each subdirectory
    for subdir in sorted(subdirs, key=lambda d: d.name):
        subdir_path = os.path.abspath(subdir.path)
        # Skip if already processed
        if subdir_path in manifest:
            torrent_file, timestamp = manifest[subdir_path]
            print(f"\nSkipping: {subdir.name} ({torrent_file}, processed at {timestamp.isoformat(timespec='seconds')})")
            continue
            
        print(f"\nProcessing: {subdir.name}")
        print("=" * (11 + len(subdir.name)))
        
        output_path = os.path.join(output_dir, f"{subdir.name}.torrent")
        try:
            torrent_path = create_torrent(subdir_path, tracker_url, output_path)
            created_torrents.append(torrent_path)
            # Append new entry to manifest immediately after successful creation
            append_to_manifest(output_dir, subdir_path, os.path.basename(torrent_path), datetime.now())
            print(f"Created torrent: {output_path}")
        except Exception as e:
            print(f"Error creating torrent for {subdir.name}:")
            print(str(e))
    
    print(f"\nComplete! Created {len(created_torrents)} new torrent files in {output_dir}/")
    print(f"Total processed: {len(manifest) + len(created_torrents)} directories")
    return created_torrents 