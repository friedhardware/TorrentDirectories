"""
File system utilities for handling paths, file operations, and size formatting.
"""
from __future__ import annotations

import os
import re
import shutil
from datetime import datetime

def is_hidden(path: str) -> bool:
    """
    Check if a file or directory is hidden.
    
    Args:
        path: Path to check
        
    Returns:
        True if the path is hidden (starts with .)
    """
    name = os.path.basename(path)
    return name.startswith('.')

def is_system_file(path: str) -> bool:
    """
    Check if a file is a system file that should be skipped.
    
    Args:
        path: Path to check
        
    Returns:
        True if the file is a system file (e.g. .DS_Store, .nfs, .smb)
    """
    system_files = {
        # macOS system files
        '.DS_Store',
        '.localized',
        '.Spotlight-V100',
        '.Trashes',
        '.fseventsd',
        '.TemporaryItems',
        '.apdisk',
        '.VolumeIcon.icns',
        '.com.apple.timemachine.donotpresent',
        
        # Network share system files
        '.smb',  # SMB temporary files
        '.nfs',  # NFS temporary files
        '.afp',  # AFP temporary files
        '.AppleDouble',  # AFP resource forks
        '.AppleDB',  # AFP database
        '.AppleDesktop',  # AFP desktop settings
        '@eaDir',  # Synology NAS extended attributes
        '.snapshot',  # ZFS snapshots
        '.zfs',  # ZFS system files
        
        # Unix/Linux system files
        '.directory',  # KDE directory settings
        '.Trash',  # Linux trash directory
        '.thumbnails',  # Thumbnail cache
        '.cache',  # Cache directory
        '.config',  # Config directory
        '.local',  # Local data directory
        '.gvfs',  # GNOME Virtual File System
        '.dbus',  # D-Bus system files
        '.pulse',  # PulseAudio files
        '.Xauthority',  # X11 authority file
        '.ICEauthority',  # ICE authority file
        
        # Temporary files
        '.tmp',
        '.temp',
        '.swp',  # Vim swap files
        '.swo',  # Vim swap files
        '.bak',  # Backup files
        '.old',  # Old files
        '.orig',  # Original files
        '.part',  # Partial downloads
        '.crdownload',  # Chrome downloads
        '.download',  # Firefox downloads
        '.aria2',  # Aria2 downloads
        '.torrent',  # Torrent files
        '.magnet'  # Magnet links
    }
    return os.path.basename(path) in system_files

def get_safe_path(path: str) -> str:
    """
    Convert a path to a safe format for use in filenames.
    
    Args:
        path: Path to convert
        
    Returns:
        Path with special characters replaced with underscores
    """
    # Replace invalid filename characters with underscores
    safe = re.sub(r'[<>:"/\\|?*]', '_', path)
    return safe

def list_files(directory: str, skip_hidden: bool = True, skip_system: bool = True) -> List[str]:
    """
    List all files in a directory recursively.
    
    Args:
        directory: Directory to scan
        skip_hidden: Whether to skip hidden files and directories
        skip_system: Whether to skip system files
        
    Returns:
        List of file paths relative to the input directory
    """
    files = []
    
    for root, dirs, filenames in os.walk(directory):
        # Filter directories
        if skip_hidden:
            dirs[:] = [d for d in dirs if not is_hidden(os.path.join(root, d))]
            
        # Filter and add files
        for filename in filenames:
            filepath = os.path.join(root, filename)
            
            if skip_hidden and is_hidden(filepath):
                continue
                
            if skip_system and is_system_file(filepath):
                continue
                
            # Get path relative to input directory
            relpath = os.path.relpath(filepath, directory)
            files.append(relpath)
            
    return sorted(files)

def get_total_size(paths: List[str]) -> int:
    """
    Calculate the total size of files.
    
    Args:
        paths: List of file paths
        
    Returns:
        Total size in bytes
    """
    return sum(os.path.getsize(p) for p in paths if os.path.exists(p))

def format_size(size_bytes: int) -> str:
    """
    Format a size in bytes to a human readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g. "1.23 GB")
    """
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if size_bytes < 1024 or unit == 'TiB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024 

def backup_file(file_path: str) -> str:
    """
    Create a backup of a file with timestamp.
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        Path to the backup file
    """
    if not os.path.exists(file_path):
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path 