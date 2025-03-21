"""
Tests for CLI utility functions.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from torrent.utils.cli_utils import list_files, parse_size


def test_parse_size_valid_units() -> None:
    """Test parsing size strings with valid units."""
    assert parse_size("1K") == 1024
    assert parse_size("1M") == 1024 * 1024
    assert parse_size("1G") == 1024 * 1024 * 1024
    assert parse_size("1T") == 1024 * 1024 * 1024 * 1024


def test_parse_size_decimal_values() -> None:
    """Test parsing size strings with decimal values."""
    assert parse_size("1.5K") == int(1.5 * 1024)
    assert parse_size("0.5M") == int(0.5 * 1024 * 1024)
    assert parse_size("2.7G") == int(2.7 * 1024 * 1024 * 1024)


def test_parse_size_no_unit() -> None:
    """Test parsing size strings without units."""
    assert parse_size("1024") == 1024
    assert parse_size("500") == 500


def test_parse_size_case_insensitive() -> None:
    """Test that unit parsing is case-insensitive."""
    assert parse_size("1k") == parse_size("1K")
    assert parse_size("1m") == parse_size("1M")
    assert parse_size("1g") == parse_size("1G")
    assert parse_size("1t") == parse_size("1T")


def test_parse_size_whitespace() -> None:
    """Test parsing size strings with whitespace."""
    assert parse_size(" 1K ") == 1024
    assert parse_size("\t1M\n") == 1024 * 1024


def test_parse_size_invalid() -> None:
    """Test parsing invalid size strings."""
    with pytest.raises(ValueError):
        parse_size("")

    with pytest.raises(ValueError):
        parse_size("invalid")

    with pytest.raises(ValueError):
        parse_size("1X")  # Invalid unit

    with pytest.raises(ValueError):
        parse_size("K")  # Missing number


def test_list_files_relative(tmp_path: Path) -> None:
    """Test listing files with relative paths."""
    # Create test directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").touch()
    (tmp_path / "dir1" / "file2.txt").touch()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file3.txt").touch()
    (tmp_path / "file4.txt").touch()

    files = list_files(tmp_path)
    assert sorted(files) == sorted(
        [
            os.path.join("dir1", "file1.txt"),
            os.path.join("dir1", "file2.txt"),
            os.path.join("dir2", "file3.txt"),
            "file4.txt",
        ]
    )


def test_list_files_absolute(tmp_path: Path) -> None:
    """Test listing files with absolute paths."""
    # Create test directory structure
    (tmp_path / "dir1").mkdir()
    file1 = tmp_path / "dir1" / "file1.txt"
    file1.touch()
    file2 = tmp_path / "file2.txt"
    file2.touch()

    files = list_files(tmp_path, relative=False)
    assert sorted(files) == sorted([str(file1), str(file2)])


def test_list_files_empty_dir(tmp_path: Path) -> None:
    """Test listing files in an empty directory."""
    assert list_files(tmp_path) == []


def test_list_files_nested_dirs(tmp_path: Path) -> None:
    """Test listing files in deeply nested directories."""
    # Create nested directory structure
    deep_dir = tmp_path / "dir1" / "dir2" / "dir3"
    deep_dir.mkdir(parents=True)
    (deep_dir / "deep_file.txt").touch()
    (tmp_path / "root_file.txt").touch()

    files = list_files(tmp_path)
    assert sorted(files) == sorted(
        [os.path.join("dir1", "dir2", "dir3", "deep_file.txt"), "root_file.txt"]
    )


def test_list_files_nonexistent_dir(tmp_path: Path) -> None:
    """Test listing files in a nonexistent directory."""
    # Test nonexistent directory
    nonexistent_dir = tmp_path / "definitely_does_not_exist"
    assert not nonexistent_dir.exists()
    with pytest.raises(FileNotFoundError):
        list_files(nonexistent_dir)

    # Test path that exists but is not a directory
    not_a_dir = tmp_path / "not_a_dir.txt"
    not_a_dir.touch()
    with pytest.raises(NotADirectoryError):
        list_files(not_a_dir)
