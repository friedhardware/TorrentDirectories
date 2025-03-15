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
        True if the path is hidden (starts with . on Unix or has hidden attribute on Windows)
    """
    name = os.path.basename(path)
    if name.startswith('.'):
        return True
        
    # Check for Windows hidden attribute
    if os.name == 'nt':
        try:
            import win32api, win32con
            attribute = win32api.GetFileAttributes(path)
            return attribute & win32con.FILE_ATTRIBUTE_HIDDEN
        except (ImportError, OSError):
            return False
            
    return False

def is_system_file(path: str) -> bool:
    """
    Check if a file is a system file that should be skipped.
    
    Args:
        path: Path to check
        
    Returns:
        True if the file is a system file (e.g. Thumbs.db, .DS_Store)
    """
    system_files = {
        'Thumbs.db',
        '.DS_Store',
        'desktop.ini',
        '$RECYCLE.BIN',
        'System Volume Information'
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