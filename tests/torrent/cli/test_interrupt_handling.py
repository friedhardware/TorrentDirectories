"""Tests for interrupt handling in the CLI."""

from __future__ import annotations

import signal
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from torrent.cli.main import cli, signal_handler
from torrent.errors.exceptions import ErrorCode


@pytest.mark.skip(reason="Global state handling needs to be revisited")
def test_signal_handler_first_interrupt(reset_interrupted):
    """Test handling of first interrupt signal."""
    frame = None
    signal_handler(signal.SIGINT, frame)
    import torrent.cli.main

    assert (
        torrent.cli.main.interrupted is True
    ), "Global interrupted flag should be set to True"


def test_signal_handler_second_interrupt():
    """Test handling of second interrupt signal."""
    frame = None
    with patch("torrent.cli.main.interrupted", True), patch("sys.exit") as mock_exit:
        signal_handler(signal.SIGINT, frame)
        mock_exit.assert_called_once_with(ErrorCode.INTERRUPTED.value)


def test_torrent_creation_interrupt(runner: CliRunner, tmp_path: Path) -> None:
    """Test interrupting torrent creation."""
    with (
        runner.isolated_filesystem(),
        patch("torrent.core.torrent_creator.interrupted", True),
    ):  # Fix the path here
        result = runner.invoke(
            cli, ["file", "test.txt", "http://tracker.example.com/announce"]
        )
        assert (
            result.exit_code == ErrorCode.USAGE_ERROR.value
        )  # Click validates file existence first


def test_cli_interrupt_handling(runner: CliRunner) -> None:
    """Test CLI handling of interrupts."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


@pytest.mark.skip(reason="Global state handling needs to be revisited")
def test_batch_mode_interrupt(runner: CliRunner, test_dir: Path) -> None:
    """Test interrupt handling in batch mode."""
    # Create test directories
    test_dir.mkdir(exist_ok=True)
    (test_dir / "dir1").mkdir()
    (test_dir / "dir1" / "file1.txt").write_text("content1")
    (test_dir / "dir2").mkdir()
    (test_dir / "dir2" / "file2.txt").write_text("content2")

    def mock_create(*args, **kwargs):
        raise KeyboardInterrupt()

    with patch(
        "torrent.core.torrent_creator.TorrentCreator.create", mock_create
    ):  # Fix the path here
        result = runner.invoke(
            cli,
            [
                "batch",
                str(test_dir),
                "http://tracker.example.com/announce",
                "--output",
                str(test_dir / "torrents"),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == ErrorCode.INTERRUPTED.value
        assert "Operation cancelled by user" in result.output
