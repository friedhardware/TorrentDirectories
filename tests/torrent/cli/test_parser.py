"""
Tests for the CLI argument parser.
"""

from __future__ import annotations

import pytest
from pytest_mock import MockerFixture

from torrent.cli.config import create_torrent_config
from torrent.cli.parser import create_parser


def test_version_argument() -> None:
    """Test that the version argument is properly configured."""
    parser = create_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])
    assert exc_info.value.code == 0


def test_file_command_required_args() -> None:
    """Test that file command requires path and tracker arguments."""
    parser = create_parser()
    args = parser.parse_args(["file", "path/to/content", "http://tracker.com/announce"])
    assert args.command == "file"
    assert args.path == "path/to/content"
    assert args.tracker == "http://tracker.com/announce"
    assert not args.force
    assert args.output is None


def test_file_command_optional_args() -> None:
    """Test optional arguments for file command."""
    parser = create_parser()
    args = parser.parse_args(
        [
            "file",
            "--force",
            "--output",
            "custom.torrent",
            "path/to/content",
            "http://tracker.com/announce",
        ]
    )
    assert args.force
    assert args.output == "custom.torrent"


def test_batch_command_required_args() -> None:
    """Test that batch command requires directory and tracker arguments."""
    parser = create_parser()
    args = parser.parse_args(["batch", "path/to/parent", "http://tracker.com/announce"])
    assert args.command == "batch"
    assert args.directory == "path/to/parent"
    assert args.tracker == "http://tracker.com/announce"
    assert not args.clean
    assert not args.force
    assert args.max_failures == 0


def test_batch_command_optional_args() -> None:
    """Test optional arguments for batch command."""
    parser = create_parser()
    args = parser.parse_args(
        [
            "batch",
            "--clean",
            "--force",
            "--max-failures",
            "5",
            "path/to/parent",
            "http://tracker.com/announce",
        ]
    )
    assert args.clean
    assert args.force
    assert args.max_failures == 5


def test_global_torrent_options() -> None:
    """Test global torrent creation options."""
    parser = create_parser()
    # Test default behavior - should skip system files by default
    args = parser.parse_args(
        [
            "--min-piece-size",
            "256K",
            "--max-piece-size",
            "32M",
            "--target-pieces",
            "1000-2000",
            "file",
            "path/to/content",
            "http://tracker.com/announce",
        ]
    )
    assert args.min_piece_size == "256K"
    assert args.max_piece_size == "32M"
    assert args.target_pieces == "1000-2000"
    assert args.skip_system_files  # Should be True by default

    # Test with include-system-files flag
    args = parser.parse_args(
        [
            "--min-piece-size",
            "256K",
            "--max-piece-size",
            "32M",
            "--target-pieces",
            "1000-2000",
            "--include-system-files",
            "file",
            "path/to/content",
            "http://tracker.com/announce",
        ]
    )
    assert not args.skip_system_files  # Should be False when --include-system-files is used


def test_global_torrent_options_large_piece_size(mocker: MockerFixture) -> None:
    """Test parsing of large piece size."""
    # Mock argparse.ArgumentParser to avoid SystemExit
    mock_parser = mocker.patch("argparse.ArgumentParser", autospec=True)
    mock_parser_instance = mock_parser.return_value

    # Test valid piece size at limit
    mock_args = mocker.Mock()
    mock_args.max_piece_size = "64M"
    mock_args.min_piece_size = None
    mock_args.target_pieces = None
    mock_args.skip_system_files = True  # Default is True
    mock_parser_instance.parse_args.return_value = mock_args

    # Test that 64M is parsed correctly
    config = create_torrent_config(mock_args)
    assert config.max_piece_size == 64 * 1024 * 1024  # 64 MiB

    # Test that piece size above limit is rejected
    mock_args.max_piece_size = "128M"
    with pytest.raises(ValueError, match="Maximum piece size cannot exceed 64 MiB"):
        create_torrent_config(mock_args)


def test_missing_required_args() -> None:
    """Test that missing required arguments raise an error."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["file"])  # Missing path and tracker
    with pytest.raises(SystemExit):
        parser.parse_args(["batch"])  # Missing directory and tracker
