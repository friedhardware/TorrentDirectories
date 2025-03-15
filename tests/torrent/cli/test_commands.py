"""
Tests for CLI command handlers.
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import Mock, patch

from torrent.cli.commands import process_single, process_batch
from torrent.utils.config import TorrentConfig

@pytest.fixture
def mock_torrent_creator():
    """Fixture for mocked TorrentCreator."""
    with patch('torrent.cli.commands.TorrentCreator') as mock:
        creator_instance = Mock()
        mock.return_value = creator_instance
        creator_instance.create_torrent.return_value = 'output.torrent'
        yield creator_instance

@pytest.fixture
def mock_manifest_manager():
    """Fixture for mocked ManifestManager."""
    with patch('torrent.cli.commands.ManifestManager') as mock:
        manager_instance = Mock()
        mock.return_value = manager_instance
        yield manager_instance

def test_process_single_success(mock_torrent_creator, sample_files, clean_env, assert_logs, caplog):
    """Test successful single file/directory processing."""
    result = process_single(
        path=str(sample_files),
        tracker_url='http://tracker.com/announce',
        output='output.torrent'
    )
    
    assert result == 0
    mock_torrent_creator.create_torrent.assert_called_once_with(
        str(sample_files), 'output.torrent'
    )

def test_process_single_dry_run(mock_torrent_creator, sample_files, assert_logs, caplog):
    """Test dry run mode for single processing."""
    result = process_single(
        path=str(sample_files),
        tracker_url='http://tracker.com/announce',
        dry_run=True
    )
    
    assert result == 0
    mock_torrent_creator.create_torrent.assert_not_called()
    assert "Would create torrent from" in caplog.text

def test_process_single_existing_output(mock_torrent_creator, sample_files, temp_dir, assert_logs, caplog):
    """Test handling of existing output file."""
    output_path = temp_dir / 'output.torrent'
    output_path.write_text('dummy')
    
    # Without force flag
    result = process_single(
        path=str(sample_files),
        tracker_url='http://tracker.com/announce',
        output=str(output_path)
    )
    assert result == 1
    mock_torrent_creator.create_torrent.assert_not_called()
    assert caplog.has_error("Output file already exists")
    
    # With force flag
    result = process_single(
        path=str(sample_files),
        tracker_url='http://tracker.com/announce',
        output=str(output_path),
        force=True
    )
    assert result == 0
    mock_torrent_creator.create_torrent.assert_called_once()

@pytest.mark.slow
def test_process_batch_success(mock_torrent_creator, mock_manifest_manager, temp_dir, assert_logs, caplog):
    """Test successful batch processing."""
    parent_dir = temp_dir / 'parent'
    parent_dir.mkdir()
    (parent_dir / 'dir1').mkdir()
    (parent_dir / 'dir2').mkdir()
    
    mock_manifest_manager.is_directory_processed.return_value = False
    
    result = process_batch(
        directory=str(parent_dir),
        tracker_url='http://tracker.com/announce'
    )
    
    assert result == 0
    assert mock_torrent_creator.create_torrent.call_count == 2
    assert mock_manifest_manager.add_entry.call_count == 2

@pytest.mark.slow
def test_process_batch_dry_run(mock_torrent_creator, mock_manifest_manager, temp_dir, assert_logs, caplog):
    """Test dry run mode for batch processing."""
    parent_dir = temp_dir / 'parent'
    parent_dir.mkdir()
    (parent_dir / 'dir1').mkdir()
    (parent_dir / 'dir2').mkdir()
    
    mock_manifest_manager.is_directory_processed.return_value = True
    
    result = process_batch(
        directory=str(parent_dir),
        tracker_url='http://tracker.com/announce',
        dry_run=True
    )
    
    assert result == 0
    mock_torrent_creator.create_torrent.assert_not_called()
    mock_manifest_manager.add_entry.assert_not_called()
    assert "Would process 2 directories" in caplog.text

@pytest.mark.slow
def test_process_batch_with_failures(mock_torrent_creator, mock_manifest_manager, temp_dir, assert_logs, caplog):
    """Test batch processing with failures."""
    parent_dir = temp_dir / 'parent'
    parent_dir.mkdir()
    (parent_dir / 'dir1').mkdir()
    (parent_dir / 'dir2').mkdir()
    (parent_dir / 'dir3').mkdir()
    
    mock_manifest_manager.is_directory_processed.return_value = False
    
    def fail_on_second(*args, **kwargs):
        if mock_torrent_creator.create_torrent.call_count == 2:
            raise ValueError("Test error")
        return 'output.torrent'
    
    mock_torrent_creator.create_torrent.side_effect = fail_on_second
    
    # With max_failures=0 (unlimited)
    result = process_batch(
        directory=str(parent_dir),
        tracker_url='http://tracker.com/announce'
    )
    assert result == 1
    assert mock_torrent_creator.create_torrent.call_count == 3
    assert caplog.has_error("Test error")
    
    # Reset mock and logs
    mock_torrent_creator.create_torrent.reset_mock()
    mock_torrent_creator.create_torrent.side_effect = fail_on_second
    caplog.clear()
    
    # With max_failures=1
    result = process_batch(
        directory=str(parent_dir),
        tracker_url='http://tracker.com/announce',
        max_failures=1
    )
    assert result == 1
    assert mock_torrent_creator.create_torrent.call_count == 2
    assert caplog.has_error("Stopping after 1 failures") 