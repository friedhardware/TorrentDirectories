"""
Tests for the CLI argument parser.
"""
from __future__ import annotations

import pytest
from torrent.cli.parser import create_parser

def test_version_argument():
    """Test that the version argument is properly configured."""
    parser = create_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(['--version'])
    assert exc_info.value.code == 0

def test_file_command_required_args():
    """Test that file command requires path and tracker arguments."""
    parser = create_parser()
    args = parser.parse_args(['file', 'path/to/content', 'http://tracker.com/announce'])
    assert args.command == 'file'
    assert args.path == 'path/to/content'
    assert args.tracker == 'http://tracker.com/announce'
    assert not args.force
    assert args.output is None

def test_file_command_optional_args():
    """Test optional arguments for file command."""
    parser = create_parser()
    args = parser.parse_args([
        'file',
        '--force',
        '--output', 'custom.torrent',
        'path/to/content',
        'http://tracker.com/announce'
    ])
    assert args.force
    assert args.output == 'custom.torrent'

def test_batch_command_required_args():
    """Test that batch command requires directory and tracker arguments."""
    parser = create_parser()
    args = parser.parse_args(['batch', 'path/to/parent', 'http://tracker.com/announce'])
    assert args.command == 'batch'
    assert args.directory == 'path/to/parent'
    assert args.tracker == 'http://tracker.com/announce'
    assert not args.clean
    assert not args.force
    assert args.manifest is None
    assert args.max_failures == 0

def test_batch_command_optional_args():
    """Test optional arguments for batch command."""
    parser = create_parser()
    args = parser.parse_args([
        'batch',
        '--clean',
        '--force',
        '--manifest', 'custom.csv',
        '--max-failures', '5',
        'path/to/parent',
        'http://tracker.com/announce'
    ])
    assert args.clean
    assert args.force
    assert args.manifest == 'custom.csv'
    assert args.max_failures == 5

def test_global_torrent_options():
    """Test global torrent creation options."""
    parser = create_parser()
    args = parser.parse_args([
        '--min-piece-size', '512K',
        '--max-piece-size', '32M',
        '--target-pieces', '500-1000',
        '--include-hidden',
        '--include-system',
        'file',
        'path/to/content',
        'http://tracker.com/announce'
    ])
    assert args.min_piece_size == '512K'
    assert args.max_piece_size == '32M'
    assert args.target_pieces == '500-1000'
    assert args.include_hidden
    assert args.include_system

def test_missing_required_args():
    """Test that missing required arguments raise an error."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['file'])  # Missing path and tracker
    with pytest.raises(SystemExit):
        parser.parse_args(['batch'])  # Missing directory and tracker 