"""Tests for interrupt handling in the CLI."""

from __future__ import annotations

import signal
from unittest.mock import patch

import click
import pytest

from torrent.cli.main import main, signal_handler
from torrent.exceptions import ErrorCode, TorrentCreationError
from torrent.manifest import ManifestManager
from torrent.torrent_creator import TorrentConfig, TorrentCreator


@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Setup and cleanup for each test."""
    global interrupted
    interrupted = False
    yield
    interrupted = False


@pytest.fixture
def mock_logger():
    """Mock the logger."""
    with patch("torrent.cli.main.logger") as mock:
        yield mock


@pytest.fixture
def mock_click():
    """Mock click functions."""
    with patch("torrent.cli.main.click") as mock:
        yield mock


def test_signal_handler_first_interrupt(mock_logger, mock_click):
    """Test handling of first interrupt signal."""
    with patch("sys.exit") as mock_exit:
        signal_handler(signal.SIGINT, None)
        mock_logger.info.assert_called_once_with("Interrupt received, cleaning up...")
        mock_click.echo.assert_called_once()
        mock_exit.assert_not_called()


def test_signal_handler_second_interrupt(mock_logger):
    """Test handling of second interrupt signal."""
    with patch("torrent.cli.main.interrupted", True), patch("sys.exit") as mock_exit:
        signal_handler(signal.SIGINT, None)
        mock_exit.assert_called_once_with(ErrorCode.INTERRUPTED.value)
        mock_logger.warning.assert_called_once_with(
            "Forced exit due to second interrupt"
        )


def test_torrent_creation_interrupt(tmp_path):
    """Test interruption during torrent creation."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "test.txt").write_text("test data")
    output_path = tmp_path / "test.torrent"

    config = TorrentConfig(tracker_url="http://example.com/announce")
    creator = TorrentCreator(config)

    def mock_set_piece_hashes(*args, **kwargs):
        raise RuntimeError("Interrupted")

    with (
        patch("libtorrent.set_piece_hashes", mock_set_piece_hashes),
        patch("torrent.torrent_creator.interrupted", True),
    ):  # Ensure the global flag is set
        with pytest.raises(TorrentCreationError) as exc_info:
            creator.create(input_dir, output_path)

    assert "Torrent creation interrupted by user" in str(exc_info.value)
    assert not output_path.exists()


def test_cli_interrupt_handling(tmp_path):
    """Test CLI handling of interrupts during torrent creation."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "test.txt").write_text("test data")
    output_path = tmp_path / "test.torrent"

    def mock_process_single(*args, **kwargs):
        signal_handler(signal.SIGINT, None)  # Set the interrupted flag
        raise click.exceptions.Abort()  # Simulate Ctrl+C

    with patch("torrent.cli.main.process_single", mock_process_single):
        try:
            main(
                [
                    "file",
                    str(input_dir),
                    "http://example.com/announce",
                    "-o",
                    str(output_path),
                ]
            )
        except SystemExit as e:
            assert e.code == ErrorCode.INTERRUPTED.value
        else:
            pytest.fail("Expected SystemExit")

    assert not output_path.exists()


def test_batch_mode_interrupt(tmp_path):
    """Test interrupt handling during batch processing."""
    # Create test directories
    parent_dir = tmp_path / "parent"
    parent_dir.mkdir()
    output_dir = tmp_path / "torrents"
    output_dir.mkdir()

    # Create test subdirectories with content
    for i in range(3):
        subdir = parent_dir / f"dir{i}"
        subdir.mkdir()
        (subdir / "test.txt").write_text(f"test data {i}")

    original_create = TorrentCreator.create

    def mock_create(self, input_path, output_path):
        # Successfully process the first directory
        if "dir0" in str(input_path):
            return original_create(self, input_path, output_path)
        # Interrupt during the second directory
        if "dir1" in str(input_path):
            signal_handler(signal.SIGINT, None)  # Set the interrupted flag
            raise click.exceptions.Abort()  # Simulate Ctrl+C
        pytest.fail("Should not process dir2")  # Should not reach dir2

    with patch("torrent.torrent_creator.TorrentCreator.create", mock_create):
        try:
            main(
                [
                    "batch",
                    str(parent_dir),
                    "http://example.com/announce",
                    "-o",
                    str(output_dir),
                ]
            )
        except SystemExit as e:
            assert e.code == ErrorCode.INTERRUPTED.value
        else:
            pytest.fail("Expected SystemExit")

    # Verify that only the first directory was processed
    assert (output_dir / "dir0.torrent").exists()
    assert not (output_dir / "dir1.torrent").exists()
    assert not (output_dir / "dir2.torrent").exists()

    # Verify manifest integrity
    manifest = ManifestManager(output_dir)
    processed = manifest.get_processed_directories()
    assert len(processed) == 1
    assert str(parent_dir / "dir0") in processed
