"""
Tests for the CLI command handlers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from torrent.cli.commands import handle_dry_run, process_batch, process_single
from torrent.exceptions import ErrorCode, TorrentError
from torrent.utils.config import TorrentConfig


@pytest.fixture
def test_config() -> TorrentConfig:
    """Create a test torrent configuration."""
    return TorrentConfig(
        tracker_url="http://example.com/announce",
        private=True,
        min_piece_size=256 * 1024,  # 256K
        max_piece_size=16 * 1024 * 1024,  # 16M
        source="test",
        comment="test comment",
    )


@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    """Create a test directory with some files."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("test content 1")
    (test_dir / "file2.txt").write_text("test content 2")
    return test_dir


def test_handle_dry_run_single_file(
    test_dir: Path, test_config: TorrentConfig, capsys: pytest.CaptureFixture
) -> None:
    """Test dry run handling for a single file."""
    test_file = test_dir / "file1.txt"
    handle_dry_run(str(test_file), None, test_config, is_batch=False)
    captured = capsys.readouterr()
    assert f"Would create torrent from: {test_file}" in captured.out
    assert f"Would save to: {test_file}.torrent" in captured.out
    assert "File size:" in captured.out
    assert "Configuration:" in captured.out
    assert "Private: True" in captured.out


def test_handle_dry_run_single_directory(
    test_dir: Path, test_config: TorrentConfig, capsys: pytest.CaptureFixture
) -> None:
    """Test dry run handling for a single directory."""
    handle_dry_run(str(test_dir), None, test_config, is_batch=False)
    captured = capsys.readouterr()
    assert f"Would create torrent from: {test_dir}" in captured.out
    assert f"Would save to: {test_dir}.torrent" in captured.out
    assert "Directory size:" in captured.out
    assert "Files that would be included" in captured.out
    assert "file1.txt" in captured.out
    assert "file2.txt" in captured.out


def test_handle_dry_run_batch(
    test_dir: Path, test_config: TorrentConfig, capsys: pytest.CaptureFixture
) -> None:
    """Test dry run handling for batch processing."""
    handle_dry_run(str(test_dir), "torrents", test_config, is_batch=True)
    captured = capsys.readouterr()
    assert f"Would process directory: {test_dir}" in captured.out
    assert "Would save torrents to: torrents" in captured.out
    assert "Total size:" in captured.out
    assert "Directories that would be processed" in captured.out


def test_handle_dry_run_nonexistent_path(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test dry run handling for nonexistent path."""
    with pytest.raises(TorrentError) as exc_info:
        handle_dry_run(str(test_dir / "nonexistent"), None, test_config, is_batch=False)
    assert exc_info.value.error_code == ErrorCode.FILE_NOT_FOUND


def test_process_single_file(test_dir: Path, test_config: TorrentConfig) -> None:
    """Test processing a single file."""
    test_file = test_dir / "file1.txt"
    output_path = test_dir / "output.torrent"
    result = process_single(
        str(test_file),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0
    assert output_path.exists()


def test_process_single_directory(test_dir: Path, test_config: TorrentConfig) -> None:
    """Test processing a single directory."""
    output_path = test_dir / "output.torrent"
    result = process_single(
        str(test_dir),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0
    assert output_path.exists()


def test_process_single_nonexistent_path(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test processing a nonexistent path."""
    result = process_single(
        str(test_dir / "nonexistent"),
        "http://example.com/announce",
        None,
        test_config,
        dry_run=False,
        force=False,
    )
    assert isinstance(result, TorrentError)
    assert result.error_code == ErrorCode.FILE_NOT_FOUND


def test_process_single_existing_output(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test processing with existing output file."""
    output_path = test_dir / "output.torrent"
    output_path.write_text("existing content")

    result = process_single(
        str(test_dir),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert isinstance(result, TorrentError)
    assert result.error_code == ErrorCode.FILE_EXISTS


def test_process_single_force_overwrite(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test force overwriting existing output file."""
    output_path = test_dir / "output.torrent"
    output_path.write_text("existing content")

    result = process_single(
        str(test_dir),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=True,
    )
    assert result == 0
    assert output_path.exists()


def test_process_batch_empty_directory(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test batch processing an empty directory."""
    result = process_batch(
        str(test_dir),
        "http://example.com/announce",
        str(test_dir / "torrents"),
        test_config,
        dry_run=False,
        force=False,
    )
    assert isinstance(result, TorrentError)
    assert result.error_code == ErrorCode.EMPTY_DIRECTORY


def test_process_batch_with_subdirs(test_dir: Path, test_config: TorrentConfig) -> None:
    """Test batch processing with subdirectories."""
    # Create test subdirectories
    for i in range(3):
        subdir = test_dir / f"subdir{i}"
        subdir.mkdir()
        (subdir / "file.txt").write_text(f"content {i}")

    output_dir = test_dir / "torrents"
    result = process_batch(
        str(test_dir),
        "http://example.com/announce",
        str(output_dir),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0
    assert output_dir.exists()
    assert len(list(output_dir.glob("*.torrent"))) == 3


def test_process_batch_with_max_failures(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test batch processing with maximum failures limit."""
    # Create test subdirectories
    for i in range(3):
        subdir = test_dir / f"subdir{i}"
        subdir.mkdir()
        (subdir / "file.txt").write_text(f"content {i}")

    output_dir = test_dir / "torrents"
    output_dir.mkdir()

    # Create an existing torrent file to trigger a failure
    (output_dir / "subdir0.torrent").write_text("existing content")

    result = process_batch(
        str(test_dir),
        "http://example.com/announce",
        str(output_dir),
        test_config,
        dry_run=False,
        force=False,
        max_failures=0,
    )
    assert isinstance(result, TorrentError)
    assert result.error_code == ErrorCode.MAX_FAILURES_EXCEEDED


def test_process_batch_with_clean(test_dir: Path, test_config: TorrentConfig) -> None:
    """Test batch processing with clean option."""
    # Create test subdirectories
    for i in range(2):
        subdir = test_dir / f"subdir{i}"
        subdir.mkdir()
        (subdir / "file.txt").write_text(f"content {i}")

    # Create output directory outside of the test directory to avoid processing it
    output_dir = test_dir.parent / "torrents"
    output_dir.mkdir()

    # Create a manifest entry for a nonexistent directory
    result = process_batch(
        str(test_dir),
        "http://example.com/announce",
        str(output_dir),
        test_config,
        dry_run=False,
        force=False,
        clean=True,
    )
    assert result == 0
    assert output_dir.exists()
    assert len(list(output_dir.glob("*.torrent"))) == 2


def test_process_single_empty_file(test_dir: Path, test_config: TorrentConfig) -> None:
    """Test processing an empty file."""
    test_file = test_dir / "empty.txt"
    test_file.touch()  # Create empty file
    output_path = test_dir / "output.torrent"

    result = process_single(
        str(test_file),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert isinstance(result, TorrentError)
    assert result.error_code == ErrorCode.NO_DATA


def test_process_single_empty_directory(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test processing an empty directory."""
    empty_dir = test_dir / "empty_dir"
    empty_dir.mkdir()
    output_path = test_dir / "output.torrent"

    result = process_single(
        str(empty_dir),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert isinstance(result, TorrentError)
    assert result.error_code == ErrorCode.NO_DATA


def test_process_single_invalid_piece_size(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test processing with invalid piece size configuration."""
    # Test with min piece size too small
    with pytest.raises(
        ValueError, match="Minimum piece size cannot be less than 16 KiB"
    ):
        test_config.min_piece_size = 8 * 1024  # 8KB (below 16KB minimum)

    # Test with max piece size too large
    with pytest.raises(ValueError, match="Maximum piece size cannot exceed 64 MiB"):
        test_config.max_piece_size = 128 * 1024 * 1024  # 128MB (above 64MB maximum)

    # Test with min > max piece size
    test_config.max_piece_size = 32 * 1024 * 1024  # Set max to 32MB first
    test_config.min_piece_size = 16 * 1024 * 1024  # Set min to 16MB
    with pytest.raises(
        ValueError, match="Maximum piece size .* cannot be less than minimum piece size"
    ):
        test_config.max_piece_size = (
            8 * 1024 * 1024
        )  # Try to set max to 8MB (below min)


def test_process_single_with_system_files(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test processing with system files."""
    # Create a .DS_Store file (common system file on macOS)
    (test_dir / ".DS_Store").write_text("system file")
    output_path = test_dir / "output.torrent"

    # First try without including system files
    test_config.include_system_files = False
    result = process_single(
        str(test_dir),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0  # Should succeed, ignoring .DS_Store

    # Now try with system files included
    test_config.include_system_files = True
    output_path = test_dir / "output2.torrent"
    result = process_single(
        str(test_dir),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0  # Should succeed, including .DS_Store


def test_process_single_with_symlinks(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test processing with symbolic links."""
    # Create a target file and a symlink to it
    target_file = test_dir / "target.txt"
    target_file.write_text("target content")
    symlink = test_dir / "link.txt"
    symlink.symlink_to(target_file)

    output_path = test_dir / "output.torrent"
    result = process_single(
        str(test_dir),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0  # Should handle symlinks correctly


def test_process_single_with_special_chars(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test processing paths with special characters."""
    special_dir = test_dir / "special!@#$%^&*()"
    special_dir.mkdir()
    (special_dir / "file.txt").write_text("content")

    output_path = test_dir / "output.torrent"
    result = process_single(
        str(special_dir),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0  # Should handle special characters correctly


def test_process_single_with_unicode(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test processing paths with unicode characters."""
    unicode_dir = test_dir / "测试目录"
    unicode_dir.mkdir()
    (unicode_dir / "文件.txt").write_text("content")

    output_path = test_dir / "output.torrent"
    result = process_single(
        str(unicode_dir),
        "http://example.com/announce",
        str(output_path),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0  # Should handle unicode characters correctly


def test_process_batch_resume_interrupted(
    test_dir: Path, test_config: TorrentConfig
) -> None:
    """Test resuming an interrupted batch process."""
    # Create test subdirectories
    for i in range(3):
        subdir = test_dir / f"subdir{i}"
        subdir.mkdir()
        (subdir / "file.txt").write_text(f"content {i}")

    output_dir = test_dir / "torrents"
    output_dir.mkdir()

    # Process first directory
    first_dir = test_dir / "subdir0"
    result = process_single(
        str(first_dir),
        "http://example.com/announce",
        str(output_dir / "subdir0.torrent"),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0

    # Now process all directories with force=True to overwrite existing files
    result = process_batch(
        str(test_dir),
        "http://example.com/announce",
        str(output_dir),
        test_config,
        dry_run=False,
        force=True,  # Use force to allow overwriting existing files
    )
    assert result == 0
    # Only count .torrent files in the root of the output directory
    torrent_files = [
        f
        for f in output_dir.glob("*.torrent")
        if f.parent == output_dir and f.stem != "torrents"
    ]
    assert len(torrent_files) == 3
    assert (output_dir / "manifest.csv").exists()


def test_process_batch_with_progress_reporting(
    test_dir: Path,
    test_config: TorrentConfig,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test batch processing with progress reporting."""
    # Create test subdirectories
    for i in range(3):
        subdir = test_dir / f"subdir{i}"
        subdir.mkdir()
        (subdir / "file.txt").write_text(f"content {i}")

    output_dir = test_dir / "torrents"
    output_dir.mkdir()

    # Process batch
    result = process_batch(
        str(test_dir),
        "http://example.com/announce",
        str(output_dir),
        test_config,
        dry_run=False,
        force=False,
    )
    assert result == 0

    # Check output for progress messages
    captured = capsys.readouterr()
    assert "Created torrent for subdir0" in captured.out
    assert "Created torrent for subdir1" in captured.out
    assert "Created torrent for subdir2" in captured.out
    assert "Processing complete" in captured.out
    assert "✓ Processed: 4" in captured.out  # Including output directory

    # Only count .torrent files in the root of the output directory
    torrent_files = [
        f
        for f in output_dir.glob("*.torrent")
        if f.parent == output_dir and f.stem != "torrents"
    ]
    assert len(torrent_files) == 3
    assert (output_dir / "manifest.csv").exists()
