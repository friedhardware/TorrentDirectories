import math
import os
import libtorrent # type: ignore
from typing import Optional

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

def create_directory_torrents(parent_dir: str, tracker_url: str, output_dir: Optional[str] = None) -> list[str]:
    """
    Create torrent files for each subdirectory in the specified directory.
    
    This function walks through a parent directory and creates a separate torrent
    file for each of its subdirectories. It skips hidden directories (those starting
    with a dot) and handles errors for individual subdirectories gracefully.
    
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
    
    # Get list of subdirectories
    subdirs = [
        d for d in os.scandir(parent_dir)
        if d.is_dir() and not d.name.startswith('.')
    ]
    
    if not subdirs:
        raise ValueError(f"No subdirectories found in {parent_dir}")
    
    print(f"Found {len(subdirs)} directories")
    created_torrents = []
    
    # Process each subdirectory
    for subdir in sorted(subdirs, key=lambda d: d.name):
        print(f"\nProcessing: {subdir.name}")
        print("=" * (11 + len(subdir.name)))
        
        output_path = os.path.join(output_dir, f"{subdir.name}.torrent")
        try:
            torrent_path = create_torrent(subdir.path, tracker_url, output_path)
            created_torrents.append(torrent_path)
            print(f"Created torrent: {output_path}")
        except Exception as e:
            print(f"Error creating torrent for {subdir.name}:")
            print(str(e))
    
    print(f"\nComplete! Created {len(created_torrents)} torrent files in {output_dir}/")
    return created_torrents 