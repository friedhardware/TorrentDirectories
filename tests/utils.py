"""
Test utilities for file and directory manipulation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Union


def create_test_files(directory: Path, files: Dict[str, Union[str, bytes]]) -> None:
    """
    Create test files in the given directory.

    Args:
        directory: Directory where files should be created
        files: Dictionary mapping filenames to their content (str or bytes)
    """
    for filename, content in files.items():
        file_path = directory / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            file_path.write_bytes(content)
        else:
            file_path.write_text(content)


def create_directory_structure(
    base_dir: Path, structure: Dict[str, Dict[str, Union[str, bytes]]]
) -> None:
    """
    Create a directory structure with files.

    Args:
        base_dir: Base directory where structure should be created
        structure: Dictionary mapping directory names to their file contents
                  Example: {"dir1": {"file1.txt": "content1", "file2.txt": "content2"}}
    """
    for dir_name, files in structure.items():
        dir_path = base_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        create_test_files(dir_path, files)


def create_sample_content(
    directory: Path, file_count: int = 3, content_prefix: str = "content"
) -> None:
    """
    Create a set of sample text files in a directory.

    Args:
        directory: Directory where files should be created
        file_count: Number of files to create
        content_prefix: Prefix for the content in each file
    """
    for i in range(file_count):
        (directory / f"file{i}.txt").write_text(f"{content_prefix}{i}")


def create_binary_file(path: Path, size_bytes: int) -> None:
    """
    Create a binary file of specified size.

    Args:
        path: Path where the file should be created
        size_bytes: Size of the file in bytes
    """
    path.write_bytes(b"0" * size_bytes)


def create_empty_files(directory: Path, count: int, prefix: str = "empty") -> None:
    """
    Create empty files in a directory.

    Args:
        directory: Directory where files should be created
        count: Number of empty files to create
        prefix: Prefix for the filenames
    """
    for i in range(count):
        (directory / f"{prefix}{i}.txt").touch()


def create_nested_directory_structure(
    base_dir: Path, depth: int, files_per_level: int = 2, content_prefix: str = "level"
) -> None:
    """
    Create a nested directory structure for testing.

    Args:
        base_dir: Base directory where structure should be created
        depth: Number of directory levels to create
        files_per_level: Number of files to create at each level
        content_prefix: Prefix for content in files
    """
    current_dir = base_dir
    for level in range(depth):
        create_sample_content(current_dir, files_per_level, f"{content_prefix}{level}_")
        current_dir = current_dir / f"level{level}"
        current_dir.mkdir(exist_ok=True)


def create_test_torrent_file(
    path: Path, content: str = "dummy torrent content"
) -> None:
    """
    Create a dummy torrent file for testing.

    Args:
        path: Path where the torrent file should be created
        content: Content to write to the torrent file
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
