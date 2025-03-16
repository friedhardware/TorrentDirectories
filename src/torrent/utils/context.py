"""Context managers for secure temporary file handling."""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Tuple

from .file_utils import FileSystem


@contextmanager
def secure_temp_file(prefix: str = "torrent_") -> Generator[Path, None, None]:
    """Create a secure temporary file that is automatically cleaned up.
    
    Args:
        prefix: Prefix for the temporary file name
        
    Yields:
        Path: Path to the secure temporary file
    """
    temp_path = FileSystem.create_secure_temp_file(prefix)
    try:
        yield temp_path
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


@contextmanager
def secure_temp_environment() -> Generator[Tuple[Path, Path], None, None]:
    """Creates both a temporary directory and file with proper cleanup.
    
    Yields:
        Tuple[Path, Path]: Paths to the temporary file and directory
    """
    temp_output = None
    try:
        temp_output = FileSystem.create_secure_temp_file("torrent_")
        with tempfile.TemporaryDirectory(prefix="torrent_") as temp_dir:
            yield Path(temp_output), Path(temp_dir)
    finally:
        if temp_output and Path(temp_output).exists():
            try:
                Path(temp_output).unlink()
            except OSError:
                pass 