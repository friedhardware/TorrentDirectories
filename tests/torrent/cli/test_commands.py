"""
Tests for CLI command handlers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest import mock

import libtorrent
import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from torrent.cli.commands import process_batch, process_single
from torrent.cli.config import TorrentConfig


@pytest.fixture
def mock_torrent_creator(mocker: MockerFixture) -> mock.MagicMock:
    """Mock the TorrentCreator class."""
    mock_obj: mock.MagicMock = mocker.patch("torrent.cli.commands.TorrentCreator")
    mock_instance = mock_obj.return_value
    mock_instance.create.return_value = "output.torrent"
    return mock_obj


@pytest.fixture
def mock_manifest_manager(mocker: MockerFixture) -> mock.MagicMock:
    """Mock the ManifestManager class."""
    mock_obj: mock.MagicMock = mocker.patch("torrent.cli.commands.ManifestManager")
    mock_instance = mock_obj.return_value
    mock_instance.is_directory_processed.return_value = False
    mock_instance.get_missing_torrents.return_value = set()
    return mock_obj


def test_process_single_success(
    mock_torrent_creator: mock.MagicMock,
    sample_files: Path,
    clean_env: None,
    assert_logs: Any,
    caplog: LogCaptureFixture,
) -> None:
    """Test successful single file/directory processing."""
    result = process_single(
        path=str(sample_files),
        tracker="http://tracker.com/announce",
        output="output.torrent",
    )

    assert result == 0
    mock_torrent_creator.return_value.create.assert_called_once_with(
        str(sample_files), "output.torrent"
    )


def test_process_single_existing_output(
    mock_torrent_creator: mock.MagicMock,
    sample_files: Path,
    temp_dir: Path,
    assert_logs: Any,
    caplog: LogCaptureFixture,
) -> None:
    """Test handling of existing output file."""
    output_path = temp_dir / "output.torrent"
    output_path.write_text("dummy")

    # Without force flag
    result = process_single(
        path=str(sample_files),
        tracker="http://tracker.com/announce",
        output=str(output_path),
    )
    assert result == 1
    mock_torrent_creator.return_value.create.assert_not_called()
    assert caplog.has_error("Output file already exists")

    # With force flag
    result = process_single(
        path=str(sample_files),
        tracker="http://tracker.com/announce",
        output=str(output_path),
        force=True,
    )
    assert result == 0
    mock_torrent_creator.return_value.create.assert_called_once()


def test_process_single_with_large_piece_size(tmp_path: Path) -> None:
    """Test creating a torrent with a large piece size."""
    # Create test directory with files
    input_dir = tmp_path / "sample"
    input_dir.mkdir()
    (input_dir / "file1.txt").write_text("test1")
    (input_dir / "file2.txt").write_text("test2")

    # Create torrent with maximum allowed piece size (64 MiB)
    config = TorrentConfig(max_piece_size=64 * 1024 * 1024)  # 64 MiB
    output_file = tmp_path / "output.torrent"
    tracker = "http://example.com/announce"

    # Process should succeed
    process_single(
        path=str(input_dir),
        output=str(output_file),
        tracker=tracker,
        config=config,
    )
    assert output_file.exists()

    # Test that piece size above limit is rejected
    with pytest.raises(ValueError, match="Maximum piece size cannot exceed 64 MiB"):
        config = TorrentConfig(max_piece_size=128 * 1024 * 1024)  # 128 MiB


@pytest.mark.slow
def test_process_batch_success(
    tmp_path: Path,
    mock_torrent_creator: mock.MagicMock,
    mock_manifest_manager: mock.MagicMock,
    caplog: LogCaptureFixture,
) -> None:
    """Test successful batch processing."""
    directory = tmp_path / "parent"
    directory.mkdir()
    (directory / "dir1").mkdir()
    (directory / "dir2").mkdir()

    mock_manifest = mock_manifest_manager.return_value
    mock_manifest.is_directory_processed.return_value = False
    mock_creator = mock_torrent_creator.return_value
    mock_creator.create.side_effect = ["torrents/dir1.torrent", "torrents/dir2.torrent"]

    result = process_batch(str(directory), "http://tracker.example.com")

    assert result == 0
    assert mock_manifest.add_entry.call_count == 2
    mock_manifest_manager.assert_called_once_with("torrents/")
    assert "dir1: Created torrents/dir1.torrent ✓" in caplog.text
    assert "dir2: Created torrents/dir2.torrent ✓" in caplog.text


@pytest.mark.slow
def test_process_batch_with_failures(
    mock_torrent_creator: mock.MagicMock,
    mock_manifest_manager: mock.MagicMock,
    temp_dir: Path,
    assert_logs: Any,
    caplog: LogCaptureFixture,
) -> None:
    """Test batch processing with failures."""
    parent_dir = temp_dir / "parent"
    parent_dir.mkdir()
    (parent_dir / "dir1").mkdir()
    (parent_dir / "dir2").mkdir()
    (parent_dir / "dir3").mkdir()
    (parent_dir / "dir4").mkdir()
    (parent_dir / "dir5").mkdir()

    mock_manifest_manager.is_directory_processed.return_value = False

    def fail_on_even(*args: Any, **kwargs: Any) -> str:
        if mock_torrent_creator.return_value.create.call_count % 2 == 0:
            raise ValueError("Test error")
        return "torrents/output.torrent"

    mock_torrent_creator.return_value.create.side_effect = fail_on_even

    # With max_failures=0 (unlimited)
    result = process_batch(
        directory=str(parent_dir), tracker="http://tracker.com/announce"
    )
    assert result == 1
    assert mock_torrent_creator.return_value.create.call_count == 5
    mock_manifest_manager.assert_called_once_with("torrents/")
    assert caplog.has_error("Test error")
    assert "Completed with" in caplog.text


def test_process_batch_with_output_dir(
    tmp_path: Path,
    mock_torrent_creator: mock.MagicMock,
    mock_manifest_manager: mock.MagicMock,
) -> None:
    """Test batch processing with output directory specified."""
    output_dir = tmp_path / "output"
    directory = tmp_path / "parent"
    directory.mkdir()
    (directory / "dir1").mkdir()
    (directory / "dir2").mkdir()

    # Set up mock returns
    mock_manifest = mock_manifest_manager.return_value
    mock_manifest.is_directory_processed.return_value = False
    mock_creator = mock_torrent_creator.return_value
    mock_creator.create.side_effect = [
        str(output_dir / "dir1.torrent"),
        str(output_dir / "dir2.torrent"),
    ]

    # Run batch processing
    result = process_batch(
        str(directory), "http://tracker.example.com", output_dir=str(output_dir)
    )

    assert result == 0
    mock_manifest_manager.assert_called_once_with(str(output_dir))
    assert mock_manifest.add_entry.call_count == 2


def test_process_batch_manifest_config(
    mock_torrent_creator: mock.MagicMock, tmp_path: Path
) -> None:
    """Test batch processing with manifest configuration."""
    # Create test directory structure
    parent_dir = tmp_path / "parent"
    parent_dir.mkdir()
    test_dir = parent_dir / "test1"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("test1")

    # Create manifest with configuration
    manifest_dir = tmp_path / "torrents"
    manifest_dir.mkdir()

    result = process_batch(
        str(parent_dir),
        "http://tracker.example.com",
        output_dir=str(manifest_dir),
    )

    assert result == 0
    assert (manifest_dir / "manifest.csv").exists()


def test_private_flag_set(tmp_path: Path) -> None:
    """Test that private flag is set correctly."""
    # Create test directory with files
    input_dir = tmp_path / "sample"
    input_dir.mkdir()
    (input_dir / "file1.txt").write_text("test1")

    # Create torrent with private flag
    config = TorrentConfig(private=True)
    output_file = tmp_path / "output.torrent"

    process_single(
        path=str(input_dir),
        output=str(output_file),
        tracker="http://example.com/announce",
        config=config,
    )

    # Verify private flag is set
    info = libtorrent.torrent_info(str(output_file))
    assert info.priv()
