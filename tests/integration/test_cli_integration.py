"""Integration tests for the CLI commands."""

import re
import subprocess
from pathlib import Path

import pytest


def run_command(cmd: list[str]) -> tuple[str, str, int]:
    """Run a command and return stdout, stderr, and return code.

    Args:
        cmd: Command and arguments as list of strings

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode


def test_version_command() -> None:
    """Test that --version returns the correct version."""
    stdout, stderr, code = run_command(["torrent-directories", "--version"])
    assert code == 0
    # Version should be in format "torrent-directories x.y.z"
    assert re.match(r"^torrent-directories \d+\.\d+\.\d+$", stdout.strip())


def test_help_command() -> None:
    """Test that --help returns usage information."""
    stdout, stderr, code = run_command(["torrent-directories", "--help"])
    assert code == 0
    assert "usage: torrent-directories" in stdout
    assert "positional arguments:" in stdout
    assert "{file,batch,client}" in stdout


def test_invalid_command() -> None:
    """Test that invalid command returns error."""
    stdout, stderr, code = run_command(["torrent-directories", "invalid"])
    assert code != 0
    assert "error:" in stderr.lower()


@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    """Create a sample directory with files for testing."""
    test_dir = tmp_path / "sample"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("test content 1")
    (test_dir / "file2.txt").write_text("test content 2")
    return test_dir


@pytest.fixture
def batch_dir(tmp_path: Path) -> Path:
    """Create a directory with multiple subdirectories for batch testing."""
    parent_dir = tmp_path / "parent"
    parent_dir.mkdir()

    # Create multiple subdirectories with files
    for i in range(1, 4):
        subdir = parent_dir / f"dir{i}"
        subdir.mkdir()
        (subdir / f"file{i}.txt").write_text(f"content {i}")

    return parent_dir


def test_file_command(sample_dir: Path, tmp_path: Path) -> None:
    """Test creating a single torrent file."""
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "-v",  # Global verbose flag
        "file",
        str(sample_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output),
    ]
    stdout, stderr, code = run_command(cmd)
    print(
        f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}"
    )  # Debug info
    assert code == 0
    assert output.exists()
    message = stdout or stderr  # Check both stdout and stderr
    assert "torrent created successfully" in message.lower()


def test_dry_run_command(sample_dir: Path, tmp_path: Path) -> None:
    """Test dry-run mode doesn't create files."""
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "--dry-run",  # Global dry-run flag
        "-v",  # Global verbose flag
        "file",
        str(sample_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output),
    ]
    stdout, stderr, code = run_command(cmd)
    print(
        f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}"
    )  # Debug info
    assert code == 0
    assert not output.exists()
    message = stdout or stderr  # Check both stdout and stderr
    assert "dry run mode" in message.lower()


def test_batch_command(batch_dir: Path, tmp_path: Path) -> None:
    """Test batch processing of multiple directories."""
    output_dir = tmp_path / "torrents"
    cmd = [
        "torrent-directories",
        "-v",
        "batch",
        str(batch_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output_dir),
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code == 0

    # Check that torrent files were created
    assert output_dir.exists()
    torrent_files = list(output_dir.glob("*.torrent"))
    assert len(torrent_files) == 3  # Should have 3 torrent files

    # Check manifest was created
    assert (output_dir / "manifest.csv").exists()


def test_batch_dry_run(batch_dir: Path, tmp_path: Path) -> None:
    """Test batch processing in dry-run mode."""
    output_dir = tmp_path / "torrents"
    cmd = [
        "torrent-directories",
        "--dry-run",
        "-v",
        "batch",
        str(batch_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output_dir),
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code == 0
    message = stdout or stderr
    assert "dry run mode" in message.lower()
    assert "would process" in message.lower()


def test_force_overwrite(sample_dir: Path, tmp_path: Path) -> None:
    """Test force flag allows overwriting existing torrent files."""
    output = tmp_path / "output.torrent"

    # Create initial torrent
    cmd1 = [
        "torrent-directories",
        "-v",
        "file",
        str(sample_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output),
    ]
    stdout1, stderr1, code1 = run_command(cmd1)
    assert code1 == 0
    assert output.exists()

    # Try to overwrite without force flag
    stdout2, stderr2, code2 = run_command(cmd1)
    assert code2 != 0
    assert "already exists" in (stdout2 or stderr2).lower()

    # Try to overwrite with force flag
    cmd3 = cmd1 + ["--force"]
    stdout3, stderr3, code3 = run_command(cmd3)
    assert code3 == 0
    assert "successfully" in (stdout3 or stderr3).lower()


def test_invalid_input_path(tmp_path: Path) -> None:
    """Test handling of non-existent input path."""
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "-v",
        "file",
        str(tmp_path / "nonexistent"),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output),
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code != 0
    assert not output.exists()
    message = stdout or stderr
    assert "error" in message.lower()


def test_batch_with_clean(batch_dir: Path, tmp_path: Path) -> None:
    """Test batch processing with clean flag."""
    output_dir = tmp_path / "torrents"
    output_dir.mkdir()

    # Create a manifest with a non-existent torrent
    manifest_path = output_dir / "manifest.csv"
    manifest_path.write_text(
        'directory_path,torrent_file,processed_at\n"/nonexistent","missing.torrent","2024-03-15T00:00:00"'
    )

    cmd = [
        "torrent-directories",
        "-v",
        "batch",
        str(batch_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output_dir),
        "--clean",
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code == 0
    message = stdout or stderr
    assert "missing torrent files" in message.lower()
    assert "created" in message.lower()
