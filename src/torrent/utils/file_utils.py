"""
File system utilities for handling paths, file operations, and size formatting.
"""

from __future__ import annotations

import fcntl
import os
import re
import shutil
from contextlib import contextmanager
from datetime import datetime
from typing import BinaryIO, Generator, List, TextIO, TypeVar, Union

T = TypeVar("T")


@contextmanager
def FileLock(
    file: Union[BinaryIO, TextIO], lock_type: int
) -> Generator[Union[BinaryIO, TextIO], None, None]:
    """
    Context manager for file locking operations.

    Args:
        file: File object to lock
        lock_type: Type of lock (fcntl.LOCK_SH or fcntl.LOCK_EX)

    Yields:
        The locked file object
    """
    fcntl.flock(file.fileno(), lock_type)
    try:
        yield file
    finally:
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)


def is_hidden(path: str) -> bool:
    """
    Check if a file or directory is hidden.

    Args:
        path: Path to check

    Returns:
        True if the path is hidden (starts with .)
    """
    name = os.path.basename(path)
    return name.startswith(".")


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
        ".DS_Store",
        ".localized",
        ".Spotlight-V100",
        ".Trashes",
        ".fseventsd",
        ".TemporaryItems",
        ".apdisk",
        ".VolumeIcon.icns",
        ".com.apple.timemachine.donotpresent",
        # Network share system files
        ".smb",  # SMB temporary files
        ".nfs",  # NFS temporary files
        ".afp",  # AFP temporary files
        ".AppleDouble",  # AFP resource forks
        ".AppleDB",  # AFP database
        ".AppleDesktop",  # AFP desktop settings
        "@eaDir",  # Synology NAS extended attributes
        ".snapshot",  # ZFS snapshots
        ".zfs",  # ZFS system files
        # Unix/Linux system files
        ".directory",  # KDE directory settings
        ".Trash",  # Linux trash directory
        ".thumbnails",  # Thumbnail cache
        ".cache",  # Cache directory
        ".config",  # Config directory
        ".local",  # Local data directory
        ".gvfs",  # GNOME Virtual File System
        ".dbus",  # D-Bus system files
        ".pulse",  # PulseAudio files
        ".Xauthority",  # X11 authority file
        ".ICEauthority",  # ICE authority file
        # Temporary files
        ".tmp",
        ".temp",
        ".swp",  # Vim swap files
        ".swo",  # Vim swap files
        ".bak",  # Backup files
        ".old",  # Old files
        ".orig",  # Original files
        ".part",  # Partial downloads
        ".crdownload",  # Chrome downloads
        ".download",  # Firefox downloads
        ".aria2",  # Aria2 downloads
        ".torrent",  # Torrent files
        ".magnet",  # Magnet links
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
    safe = re.sub(r'[<>:"/\\|?*]', "_", path)
    return safe


def list_files(
    directory: str, skip_hidden: bool = True, skip_system: bool = True
) -> List[str]:
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


def get_total_size(paths: list[str]) -> int:
    """
    Calculate the total size of files.

    Args:
        paths: List of file paths

    Returns:
        Total size in bytes
    """
    return sum(os.path.getsize(p) for p in paths if os.path.exists(p))


def format_size(size: int) -> str:
    """
    Format a size in bytes to a human readable string.

    Args:
        size: Size in bytes

    Returns:
        Formatted string (e.g. "1.23 GB")
    """
    size_float = float(size)  # Convert to float for division
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size_float < 1024 or unit == "TiB":
            return f"{size_float:.2f} {unit}"
        size_float /= 1024
    return f"{size_float:.2f} TiB"  # Fallback return for extremely large sizes


def backup_file(file_path: str) -> str | None:
    """
    Create a backup of a file with timestamp.

    Args:
        file_path: Path to the file to backup

    Returns:
        Path to the backup file, or None if the file doesn't exist
    """
    if not os.path.exists(file_path):
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak_{timestamp}"

    # Copy the file and ensure it's synced to disk
    with open(file_path, "rb") as src, open(backup_path, "wb") as dst:
        shutil.copyfileobj(src, dst)
        sync_to_disk(dst)

    return backup_path


def sync_to_disk(file_obj: Union[TextIO, int, BinaryIO]) -> None:
    """
    Ensure file contents are written to disk.

    Args:
        file_obj: A file object (text or binary) or file descriptor

    This function will flush file buffers and force the OS to write to disk.
    For file objects, it will call both flush() and fsync().
    For file descriptors, it will just call fsync().
    """
    if isinstance(file_obj, int):
        os.fsync(file_obj)
    else:
        file_obj.flush()
        os.fsync(file_obj.fileno())
