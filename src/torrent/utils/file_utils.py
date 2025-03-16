"""
File system utilities for torrent operations.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterator


class PathSecurity:
    """Security-related path operations."""

    @staticmethod
    def has_control_characters(path: Path) -> bool:
        """Check if a path contains control characters."""
        return any(ord(c) < 32 for c in str(path))

    @staticmethod
    def contains_special_entries(path: Path) -> bool:
        """
        Check if a path contains special directory entries that could lead to path traversal.
        Allows hidden files (starting with single '.') but blocks path traversal attempts.

        This method checks for:
        1. Path components that are exactly '.' or '..'
        2. Normalized path components that would traverse up directories
        3. Any sneaky attempts at path traversal using combinations of slashes and dots

        Args:
            path: The path to check.

        Returns:
            True if the path contains special entries that could lead to traversal, False otherwise.
        """
        # Convert to string for normalization
        path_str = str(path)

        # Check each path component for exactly '.' or '..'
        for part in path.parts:
            if part in {".", ".."}:
                return True

        # Normalize the path to catch sneaky traversal attempts
        # This handles cases like 'a/../../b', '/./a', 'a/../b', etc.
        normalized = os.path.normpath(path_str)
        normalized_parts = normalized.split(os.sep)

        # After normalization, check if:
        # 1. Any component is exactly '..'
        # 2. Contains /../ sequences (path traversal)
        # 3. Contains /./ sequences (current directory reference)
        return ".." in normalized_parts or "/../" in normalized or "/./" in normalized

    @staticmethod
    def is_within_directory(path: Path, base_dir: Path) -> bool:
        """Check if a path is within a base directory."""
        try:
            path.relative_to(base_dir)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_special_file(path: Path) -> bool:
        """Check if a path points to a special file."""
        try:
            mode = path.stat().st_mode
            return (
                stat.S_ISBLK(mode)
                or stat.S_ISCHR(mode)
                or stat.S_ISFIFO(mode)
                or stat.S_ISSOCK(mode)
            )
        except (OSError, AttributeError):
            return False

    @staticmethod
    def has_symlinks_in_chain(path: Path) -> bool:
        """Check if a path has symlinks in its resolution chain."""
        try:
            current = path
            while True:
                if current.is_symlink():
                    return True
                parent = current.parent
                if parent == current:
                    break
                current = parent
            return False
        except OSError:
            return True

    @staticmethod
    def is_safe_path(path: Path, base_dir: Path) -> bool:
        """Check if a path is safe to use."""
        return (
            not PathSecurity.has_control_characters(path)
            and not PathSecurity.contains_special_entries(path)
            and PathSecurity.is_within_directory(path, base_dir)
            and not PathSecurity.is_special_file(path)
            and not PathSecurity.has_symlinks_in_chain(path)
        )


class FileSystem:
    """File system operations."""

    @staticmethod
    def list_files(
        directory: Path,
        include_system: bool = False,
    ) -> Iterator[Path]:
        """
        List all files in a directory recursively, excluding hidden files and directories.

        Args:
            directory: The directory to list files from
            include_system: Whether to include system files (e.g. device files)

        Returns:
            Iterator of Path objects for each file
        """
        for root, dirs, files in os.walk(directory):
            # Always exclude hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file in files:
                # Skip hidden files
                if file.startswith("."):
                    continue

                file_path = Path(root) / file

                # Skip system files if requested
                if not include_system and FileSystem.is_special_file(file_path):
                    continue

                yield file_path

    @staticmethod
    def is_system_file(path: Path) -> bool:
        """Check if a file is a system file."""
        # Implementation depends on OS
        if os.name == "nt":
            try:
                attrs = path.stat().st_file_attributes
                return bool(attrs & stat.FILE_ATTRIBUTE_SYSTEM)
            except (AttributeError, OSError):
                return False
        return False

    @staticmethod
    def get_total_size(paths: Iterator[Path]) -> int:
        """Calculate total size of files."""
        return sum(path.stat().st_size for path in paths if path.is_file())

    @staticmethod
    def create_secure_temp_file(prefix: str) -> Path:
        """Create a secure temporary file."""
        fd, path = tempfile.mkstemp(prefix=prefix)
        os.close(fd)
        temp_path = Path(path)
        temp_path.chmod(0o600)  # Read/write for owner only
        return temp_path


class FileNaming:
    """File name operations."""

    @staticmethod
    def sanitize_filename(
        filename: str,
        preserve_dots: bool = False,
        preserve_case: bool = False,
    ) -> str:
        """Sanitize a filename for safe usage."""
        # Remove or replace invalid characters
        valid_chars = (
            "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )
        sanitized = "".join(c for c in filename if c in valid_chars)

        # Handle case preservation
        if not preserve_case:
            sanitized = sanitized.lower()

        # Handle dots
        if preserve_dots and filename.startswith("."):
            sanitized = "." + sanitized.lstrip(".")

        # Ensure we have a valid filename
        sanitized = sanitized.strip()
        if not sanitized:
            sanitized = "unnamed"

        return sanitized

    @staticmethod
    def format_size(size: int) -> str:
        """Format a size in bytes to human readable string."""
        for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} EiB"


# For backward compatibility
def sanitize_filename(*args, **kwargs) -> str:
    """Backward compatible wrapper for FileNaming.sanitize_filename."""
    return FileNaming.sanitize_filename(*args, **kwargs)


def is_safe_path(*args, **kwargs) -> bool:
    """Backward compatible wrapper for PathSecurity.is_safe_path."""
    return PathSecurity.is_safe_path(*args, **kwargs)


def create_secure_temp_file(*args, **kwargs) -> Path:
    """Backward compatible wrapper for FileSystem.create_secure_temp_file."""
    return FileSystem.create_secure_temp_file(*args, **kwargs)


def format_size(*args, **kwargs) -> str:
    """Backward compatible wrapper for FileNaming.format_size."""
    return FileNaming.format_size(*args, **kwargs)


def get_total_size(*args, **kwargs) -> int:
    """Backward compatible wrapper for FileSystem.get_total_size."""
    return FileSystem.get_total_size(*args, **kwargs)


def list_files(*args, **kwargs) -> Iterator[Path]:
    """Backward compatible wrapper for FileSystem.list_files."""
    return FileSystem.list_files(*args, **kwargs)


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
    shutil.copy2(file_path, backup_path)
    return backup_path
