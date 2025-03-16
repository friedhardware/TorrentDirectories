"""
Integration tests for security features of the TorrentCreator class.

Tests cover:
1. Symlink protection
2. Path sanitization
3. Secure temporary file handling
4. POSIX-specific security features
"""

import os
import stat
import socket
import tempfile
from pathlib import Path
import logging

import pytest
import libtorrent

from torrent.torrent_creator import TorrentCreator
from torrent.utils.config import TorrentConfig
from torrent.exceptions import ValidationError, CreationError

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

@pytest.fixture
def creator():
    """Create a TorrentCreator instance with default settings."""
    return TorrentCreator("http://tracker.example.com/announce")

def test_symlink_outside_directory(temp_dir, creator):
    """Test that symlinks pointing outside the input directory are rejected."""
    # Create a file outside the input directory
    outside_file = temp_dir / "outside.txt"
    outside_file.write_text("outside content")
    
    # Create input directory
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    
    # Create a symlink inside input directory pointing to outside file
    symlink_path = input_dir / "symlink.txt"
    symlink_path.symlink_to(outside_file)
    
    # Attempt to create torrent
    output_path = temp_dir / "output.torrent"
    
    with pytest.raises(ValidationError, match="No files added"):
        creator.create(input_dir, output_path)

def verify_torrent_contents(torrent_data: bytes, expected_files: list[tuple[str, int]]) -> None:
    """
    Verify that a torrent contains exactly the expected files.
    
    Args:
        torrent_data: Raw torrent file data
        expected_files: List of (filename, size) tuples
    """
    info = libtorrent.bdecode(torrent_data)[b"info"]
    
    # Handle single file case
    if b"files" not in info:
        assert len(expected_files) == 1, "Single file torrent should have exactly one file"
        name, size = expected_files[0]
        assert info[b"name"].decode() == name, f"Expected file name {name}, got {info[b'name'].decode()}"
        assert info[b"length"] == size, f"Expected size {size}, got {info[b'length']}"
        return
        
    # Handle multi-file case
    torrent_files = info[b"files"]
    assert len(torrent_files) == len(expected_files), \
        f"Expected {len(expected_files)} files, got {len(torrent_files)}"
    
    # Sort both lists by path for comparison
    torrent_files = sorted(torrent_files, key=lambda x: x[b"path"][0])
    expected_files = sorted(expected_files, key=lambda x: x[0])
    
    for torrent_file, (name, size) in zip(torrent_files, expected_files):
        # For multi-file torrents, the path is a list of components
        path_parts = [p.decode() for p in torrent_file[b"path"]]
        full_path = "/".join(path_parts)
        assert full_path == name, f"Expected path {name}, got {full_path}"
        assert torrent_file[b"length"] == size, \
            f"Expected size {size} for {name}, got {torrent_file[b'length']}"

def test_path_traversal_protection(temp_dir, creator):
    """Test protection against path traversal attempts."""
    # Create a directory structure
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    
    # Create a file outside the input directory
    outside_file = temp_dir / "outside.txt"
    outside_file.write_text("malicious content")
    
    # Create a file inside the input directory
    safe_file = input_dir / "safe.txt"
    safe_file.write_text("safe content")
    
    # Create a symlink using path traversal
    symlink_path = input_dir / "evil.txt"
    symlink_path.symlink_to(Path("..") / "outside.txt")
    
    # Attempt to create torrent
    output_path = temp_dir / "output.torrent"
    
    # The symlink should be skipped, but the safe file should be included
    result = creator.create(input_dir, output_path)
    assert Path(result).exists()
    
    # Verify torrent contents
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [("safe.txt", len("safe content"))])

def test_control_characters_in_path(temp_dir, creator):
    """Test that paths containing control characters are rejected."""
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    
    # Create a file with control character in name
    bad_file = input_dir / f"bad{chr(0x01)}file.txt"
    bad_file.write_text("content")
    
    # Create a legitimate file as well
    safe_file = input_dir / "safe.txt"
    safe_file.write_text("safe content")
    
    output_path = temp_dir / "output.torrent"
    result = creator.create(input_dir, output_path)
    
    # Verify torrent contents
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [("safe.txt", len("safe content"))])

def test_secure_temp_file_permissions(temp_dir, creator):
    """Test that temporary files are created with secure permissions."""
    input_file = temp_dir / "input.txt"
    input_file.write_text("test content")
    
    output_path = temp_dir / "output.torrent"
    result = creator.create(input_file, output_path)
    
    # Check output file permissions
    perms = stat.S_IMODE(os.stat(output_path).st_mode)
    
    # Should only be readable/writable by owner
    assert perms & stat.S_IRUSR  # Owner can read
    assert perms & stat.S_IWUSR  # Owner can write
    assert not (perms & stat.S_IRWXG)  # Group has no permissions
    assert not (perms & stat.S_IRWXO)  # Others have no permissions
    
    # Check that the file is owned by the current user
    stat_info = os.stat(output_path)
    assert stat_info.st_uid == os.getuid()
    
    # Verify no world-writable parent directories
    parent_perms = stat.S_IMODE(os.stat(output_path.parent).st_mode)
    assert not (parent_perms & stat.S_IWOTH)

def test_special_file_rejection(temp_dir, creator):
    """Test that special files (devices, sockets) are rejected."""
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    
    # Create a FIFO file (named pipe)
    fifo_path = input_dir / "test.fifo"
    os.mkfifo(fifo_path)
    
    # Create a legitimate file as well
    safe_file = input_dir / "safe.txt"
    safe_file.write_text("safe content")
    
    output_path = temp_dir / "output.torrent"
    result = creator.create(input_dir, output_path)
    
    # Verify torrent contents
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [("safe.txt", len("safe content"))])

def test_cleanup_on_error(temp_dir, creator):
    """Test that temporary files are cleaned up on error."""
    input_file = temp_dir / "input.txt"
    input_file.write_text("test content")
    
    # Create an unwritable output directory
    output_dir = temp_dir / "locked"
    output_dir.mkdir()
    os.chmod(output_dir, 0o444)  # Read-only
    
    output_path = output_dir / "output.torrent"
    
    with pytest.raises(CreationError):
        creator.create(input_file, output_path)
    
    # Check that no temporary files were left behind
    temp_files = list(temp_dir.glob("torrent_*"))
    assert len(temp_files) == 0, f"Found leftover temporary files: {temp_files}"

def test_multiple_symlink_chain(temp_dir, creator):
    """Test handling of chains of symlinks."""
    # Create a chain of symlinks
    content_file = temp_dir / "content.txt"
    content_file.write_text("test content")
    
    link1 = temp_dir / "link1"
    link2 = temp_dir / "link2"
    link3 = temp_dir / "link3"
    
    link1.symlink_to(content_file)
    link2.symlink_to(link1)
    link3.symlink_to(link2)
    
    # Create a directory with the symlink chain
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    final_link = input_dir / "chain.txt"
    final_link.symlink_to(link3)
    
    # Create a legitimate file as well
    safe_file = input_dir / "safe.txt"
    safe_file.write_text("safe content")
    
    # Try to create torrent from the directory
    output_path = temp_dir / "output.torrent"
    
    # The symlink chain should be skipped, but the safe file should be included
    result = creator.create(input_dir, output_path)
    assert Path(result).exists()
    
    # Verify torrent contents
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [("safe.txt", len("safe content"))])

def test_relative_symlink_inside_directory(temp_dir, creator):
    """Test that symlinks are skipped, even if they point to files within the input directory."""
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    
    # Create a file and a relative symlink to it
    content_file = input_dir / "content.txt"
    content_file.write_text("test content")
    
    link = input_dir / "link.txt"
    link.symlink_to(Path("content.txt"))
    
    # Create torrent - only the original file should be included
    output_path = temp_dir / "output.torrent"
    result = creator.create(input_dir, output_path)
    
    # Verify torrent contents - only the original file should be included
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [
            ("content.txt", len("test content"))
        ])

def test_unix_special_files(temp_dir: Path, creator: TorrentCreator) -> None:
    """Test handling of various POSIX special files."""
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    
    # Create a regular file for comparison
    safe_file = input_dir / "safe.txt"
    safe_file.write_text("safe content")
    
    # Create various special files
    fifo_path = input_dir / "test.fifo"
    os.mkfifo(fifo_path)
    
    socket_path = input_dir / "test.sock"
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(socket_path))
    
    # Note: Creating device files requires root privileges, so we'll just check their handling
    # if they exist in /dev
    dev_null = Path("/dev/null")
    dev_zero = Path("/dev/zero")
    if dev_null.exists() and dev_zero.exists():
        os.symlink(dev_null, input_dir / "null")
        os.symlink(dev_zero, input_dir / "zero")
    
    output_path = temp_dir / "output.torrent"
    result = creator.create(input_dir, output_path)
    
    # Verify torrent contents - only the safe file should be included
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [("safe.txt", len("safe content"))])
    
    # Clean up
    sock.close()

def test_hardlink_handling(temp_dir: Path, creator: TorrentCreator) -> None:
    """Test handling of hard links."""
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    
    # Create original file
    original = input_dir / "original.txt"
    original.write_text("test content")
    
    # Create hard link
    hardlink = input_dir / "hardlink.txt"
    os.link(original, hardlink)
    
    output_path = temp_dir / "output.torrent"
    result = creator.create(input_dir, output_path)
    
    # Both files should be included since they're regular files
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [
            ("original.txt", len("test content")),
            ("hardlink.txt", len("test content"))
        ])
    
    # Verify they have the same inode
    assert os.stat(original).st_ino == os.stat(hardlink).st_ino

def test_special_permission_bits(temp_dir: Path, creator: TorrentCreator) -> None:
    """Test handling of files with special permission bits."""
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    
    # Create files with various permissions
    regular_file = input_dir / "regular.txt"
    regular_file.write_text("regular content")
    
    executable = input_dir / "executable.sh"
    executable.write_text("#!/bin/sh\necho test")
    executable.chmod(0o755)
    
    setuid_file = input_dir / "setuid"
    setuid_file.write_text("setuid content")
    try:
        # Try to set setuid bit (might fail without root)
        setuid_file.chmod(0o4755)
    except PermissionError:
        pass
    
    output_path = temp_dir / "output.torrent"
    result = creator.create(input_dir, output_path)
    
    # All regular files should be included regardless of permissions
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [
            ("regular.txt", len("regular content")),
            ("executable.sh", len("#!/bin/sh\necho test")),
            ("setuid", len("setuid content"))
        ])

def test_hidden_files(temp_dir: Path, creator: TorrentCreator) -> None:
    """Test that hidden files and directories are excluded from the torrent."""
    # Create a visible file
    visible_file = temp_dir / "visible.txt"
    visible_file.write_text("visible content")
    
    # Create a hidden file
    hidden_file = temp_dir / ".hidden"
    hidden_file.write_text("hidden content")
    
    # Create a hidden directory with a file
    hidden_dir = temp_dir / ".config"
    hidden_dir.mkdir()
    settings_file = hidden_dir / "settings.txt"
    settings_file.write_text("settings content")
    
    output_path = temp_dir / "output.torrent"
    result = creator.create(temp_dir, output_path)
    
    # Verify that only the visible file is included
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [
            ("visible.txt", len("visible content")),
        ])

def test_special_directory_entries(temp_dir: Path, creator: TorrentCreator) -> None:
    """Test handling of paths starting with '.' or '..'."""
    logger = logging.getLogger(__name__)
    
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    logger.debug(f"Created input directory: {input_dir}")
    
    # Create a regular file
    test_file = input_dir / "test.txt"
    test_file.write_text("test content")
    logger.debug(f"Created test file: {test_file}")
    
    # Create a subdirectory with a regular file
    subdir = input_dir / "subdir"
    subdir.mkdir()
    sub_file = subdir / "sub.txt"
    sub_file.write_text("sub content")
    logger.debug(f"Created sub file: {sub_file}")
    
    # Create files starting with . and ..
    dot_file = input_dir / ".hidden.txt"
    dotdot_file = input_dir / "..hidden.txt"
    
    logger.debug(f"Creating dot files: {dot_file}, {dotdot_file}")
    dot_file.write_text("hidden content")
    dotdot_file.write_text("hidden content")
    
    # Create a hidden directory with a file
    hidden_dir = input_dir / ".config"
    hidden_dir.mkdir()
    hidden_file = hidden_dir / "settings.txt"
    hidden_file.write_text("settings content")
    logger.debug(f"Created hidden directory with file: {hidden_file}")
    
    output_path = temp_dir / "output.torrent"
    result = creator.create(input_dir, output_path)
    
    # Only regular files should be included
    with open(result, "rb") as f:
        verify_torrent_contents(f.read(), [
            ("test.txt", len("test content")),
            ("subdir/sub.txt", len("sub content")),
        ]) 