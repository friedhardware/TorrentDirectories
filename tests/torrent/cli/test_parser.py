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


def test_general_options() -> None:
    """Test general options that come before the command."""
    parser = create_parser()
    args = parser.parse_args([
        "-v",
        "--log-file", "test.log",
        "--dry-run",
        "file",
        "path/to/content",
        "http://tracker.com/announce"
    ])
    assert args.verbose
    assert args.log_file == "test.log"
    assert args.dry_run


def test_file_command_required_args() -> None:
    """Test that file command requires path and tracker arguments."""
    parser = create_parser()
    args = parser.parse_args(["file", "path/to/content", "http://tracker.com/announce"])
    assert args.command == "file"
    assert args.path == "path/to/content"
    assert args.tracker == "http://tracker.com/announce"
    assert not args.force
    assert args.output is None


def test_file_command_all_options() -> None:
    """Test all available options for file command."""
    parser = create_parser()
    args = parser.parse_args([
        "file",
        "path/to/content",
        "http://tracker.com/announce",
        "--force",
        "--output", "custom.torrent",
        "--min-piece-size", "256K",
        "--max-piece-size", "32M",
        "--target-pieces", "1000-2000",
        "--include-system",
        "--private"
    ])
    assert args.force
    assert args.output == "custom.torrent"
    assert args.min_piece_size == "256K"
    assert args.max_piece_size == "32M"
    assert args.target_pieces == "1000-2000"
    assert args.include_system
    assert args.private
    assert not args.public


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


def test_batch_command_all_options() -> None:
    """Test all available options for batch command."""
    parser = create_parser()
    args = parser.parse_args([
        "batch",
        "path/to/parent",
        "http://tracker.com/announce",
        "--clean",
        "--force",
        "--max-failures", "5",
        "--output", "output_dir",
        "--min-piece-size", "256K",
        "--max-piece-size", "32M",
        "--target-pieces", "1000-2000",
        "--include-system",
        "--public"
    ])
    assert args.clean
    assert args.force
    assert args.max_failures == 5
    assert args.output == "output_dir"
    assert args.min_piece_size == "256K"
    assert args.max_piece_size == "32M"
    assert args.target_pieces == "1000-2000"
    assert args.include_system
    assert args.public
    assert not args.private


def test_mutually_exclusive_private_public() -> None:
    """Test that --private and --public flags are mutually exclusive."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "file",
            "path/to/content",
            "http://tracker.com/announce",
            "--private",
            "--public"
        ])


def test_missing_required_args() -> None:
    """Test that missing required arguments raise an error."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["file"])  # Missing path and tracker
    with pytest.raises(SystemExit):
        parser.parse_args(["batch"])  # Missing directory and tracker
