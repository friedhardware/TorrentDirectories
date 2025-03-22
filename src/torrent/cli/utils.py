"""
Utility functions for the CLI package.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Union

import click


def parse_size(size_str: str) -> int:
    """Parse a size string with units into bytes.

    Args:
        size_str: Size string with units (e.g. '16K', '1M', '2G')

    Returns:
        Size in bytes

    Raises:
        ValueError: If the size string is invalid
    """
    units = {
        "K": 1024,
        "M": 1024 * 1024,
        "G": 1024 * 1024 * 1024,
        "T": 1024 * 1024 * 1024 * 1024,
    }

    size_str = size_str.strip().upper()
    if not size_str:
        raise ValueError("Empty size string")

    if size_str[-1] in units:
        number = float(size_str[:-1])
        unit = size_str[-1]
        return int(number * units[unit])
    else:
        return int(size_str)


def list_files(path: Union[str, Path], relative: bool = True) -> List[str]:
    """List all files in a directory recursively.

    Args:
        path: Directory path
        relative: Whether to return relative paths

    Returns:
        List of file paths

    Raises:
        FileNotFoundError: If the directory does not exist
        NotADirectoryError: If the path exists but is not a directory
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Directory does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    files = []
    for root, _, filenames in os.walk(path):
        for filename in filenames:
            file_path = Path(root) / filename
            if relative:
                files.append(str(file_path.relative_to(path)))
            else:
                files.append(str(file_path))
    return sorted(files)


def log_to_console(message: str, **kwargs: Any) -> None:
    """Log a message to the console using click.echo().

    Args:
        message: The message to log
        **kwargs: Additional keyword arguments to pass to click.echo()
    """
    click.echo(message, **kwargs)
