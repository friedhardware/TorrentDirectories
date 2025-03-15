"""
Tests for the main CLI entry point.
"""
from __future__ import annotations

import logging
import pytest
from unittest.mock import patch, Mock

from torrent.cli.main import main, setup_logging

def test_setup_logging_default():
    """Test default logging setup."""
    setup_logging()
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0], logging.StreamHandler)

def test_setup_logging_verbose():
    """Test verbose logging setup."""
    setup_logging(verbose=True)
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    handler = root_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert '%(levelname)s' in handler.formatter._fmt

def test_setup_logging_with_file(tmp_path):
    """Test logging setup with file output."""
    log_file = str(tmp_path / 'test.log')
    setup_logging(log_file=log_file)
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 2
    assert any(isinstance(h, logging.FileHandler) for h in root_logger.handlers)

@patch('torrent.cli.main.process_single')
def test_main_file_command(mock_process):
    """Test main function with file command."""
    mock_process.return_value = 0
    args = [
        'file',
        'path/to/content',
        'http://tracker.com/announce'
    ]
    
    assert main(args) == 0
    mock_process.assert_called_once()

@patch('torrent.cli.main.process_batch')
def test_main_batch_command(mock_process):
    """Test main function with batch command."""
    mock_process.return_value = 0
    args = [
        'batch',
        'path/to/parent',
        'http://tracker.com/announce'
    ]
    
    assert main(args) == 0
    mock_process.assert_called_once()

@patch('torrent.cli.main.create_torrent_config')
def test_main_config_error(mock_config):
    """Test main function handling config error."""
    mock_config.side_effect = ValueError("Test error")
    args = [
        'file',
        'path/to/content',
        'http://tracker.com/announce'
    ]
    
    assert main(args) == 1

@patch('torrent.cli.main.process_single')
def test_main_command_error(mock_process):
    """Test main function handling command error."""
    mock_process.side_effect = Exception("Test error")
    args = [
        'file',
        'path/to/content',
        'http://tracker.com/announce'
    ]
    
    assert main(args) == 1

def test_main_invalid_command():
    """Test main function with invalid command."""
    args = ['invalid']
    with pytest.raises(SystemExit) as exc_info:
        main(args)
    assert exc_info.value.code == 2

@patch('torrent.cli.main.process_single')
def test_main_verbose_error_handling(mock_process, caplog, capsys):
    """Test verbose error handling in main function."""
    mock_process.side_effect = Exception("Test error")
    args = [
        '--verbose',
        'file',
        'path/to/content',
        'http://tracker.com/announce'
    ]
    
    with caplog.at_level(logging.DEBUG):
        assert main(args) == 1
        captured = capsys.readouterr()
        assert "Unexpected error: Test error" in captured.err
        assert "Traceback" in captured.err 