"""Tests for the exceptions module."""

from pathlib import Path

from torrent.exceptions import (
    BatchProcessingError,
    DirectoryNotFoundError,
    ErrorCode,
    InvalidConfigError,
    InvalidDirectoryStructureError,
    InvalidMetadataError,
    InvalidTrackerURLError,
    ManifestError,
    MaxFailuresExceededError,
    MissingTorrentFilesError,
    NoDataError,
    NoSubdirectoriesError,
    OutputFileExistsError,
    PieceSizeError,
    TorrentCreationError,
    TorrentError,
    TorrentFileNotFoundError,
    TorrentPermissionError,
    TorrentVerificationError,
)


def test_error_code_values() -> None:
    """Test that error codes have correct values."""
    assert ErrorCode.SUCCESS.value == 0
    assert ErrorCode.ERROR.value == 1
    assert ErrorCode.USAGE_ERROR.value == 2
    assert ErrorCode.NO_DATA.value == 10
    assert ErrorCode.EMPTY_DIRECTORY.value == 11
    assert ErrorCode.FILE_EXISTS.value == 12
    assert ErrorCode.FILE_NOT_FOUND.value == 13
    assert ErrorCode.INVALID_CONFIG.value == 20
    assert ErrorCode.CREATION_ERROR.value == 21
    assert ErrorCode.TORRENT_CREATION_ERROR.value == 22
    assert ErrorCode.BATCH_PROCESSING_ERROR.value == 23
    assert ErrorCode.MAX_FAILURES_EXCEEDED.value == 24
    assert ErrorCode.INVALID_TRACKER_URL.value == 25
    assert ErrorCode.INVALID_METADATA.value == 26
    assert ErrorCode.INVALID_PIECE_SIZE.value == 27
    assert ErrorCode.NO_SUBDIRECTORIES.value == 5
    assert ErrorCode.MISSING_TORRENT_FILES.value == 6
    assert ErrorCode.DIRECTORY_NOT_FOUND.value == 8


def test_base_torrent_error() -> None:
    """Test TorrentError base class."""
    # Test without details
    error = TorrentError("test message")
    assert str(error) == "test message"
    assert error.message == "test message"
    assert error.error_code == ErrorCode.ERROR
    assert error.details == {}

    # Test with details
    details = {"key": "value"}
    error = TorrentError("test message", ErrorCode.SUCCESS, details)
    assert str(error) == "test message (details: {'key': 'value'})"
    assert error.message == "test message"
    assert error.error_code == ErrorCode.SUCCESS
    assert error.details == details


def test_no_data_error() -> None:
    """Test NoDataError exception."""
    # Test file case
    error = NoDataError("/path/to/file")
    assert str(error) == "File /path/to/file contains no data"
    assert error.error_code == ErrorCode.NO_DATA

    # Test directory case
    error = NoDataError("/path/to/dir", is_directory=True)
    assert str(error) == "Directory /path/to/dir contains no data"
    assert error.error_code == ErrorCode.NO_DATA


def test_output_file_exists_error() -> None:
    """Test OutputFileExistsError exception."""
    error = OutputFileExistsError("/path/to/file")
    assert str(error) == "Output file already exists: /path/to/file"
    assert error.error_code == ErrorCode.FILE_EXISTS


def test_torrent_creation_error() -> None:
    """Test TorrentCreationError exception."""
    # Test without details
    error = TorrentCreationError("creation failed")
    assert str(error) == "creation failed"
    assert error.error_code == ErrorCode.TORRENT_CREATION_ERROR
    assert error.details == {}

    # Test with details
    details = {"reason": "invalid data"}
    error = TorrentCreationError("creation failed", details)
    assert str(error) == "creation failed (details: {'reason': 'invalid data'})"
    assert error.details == details


def test_invalid_config_error() -> None:
    """Test InvalidConfigError exception."""
    error = InvalidConfigError("bad config")
    assert str(error) == "Invalid configuration: bad config"
    assert error.error_code == ErrorCode.INVALID_CONFIG


def test_torrent_verification_error() -> None:
    """Test TorrentVerificationError exception."""
    # Test without details
    error = TorrentVerificationError("verification failed")
    assert str(error) == "verification failed"
    assert error.error_code == ErrorCode.TORRENT_CREATION_ERROR

    # Test with details
    details = {"expected": "hash1", "actual": "hash2"}
    error = TorrentVerificationError("verification failed", details)
    assert error.details == details


def test_torrent_file_not_found_error() -> None:
    """Test TorrentFileNotFoundError exception."""
    # Test with string path
    error = TorrentFileNotFoundError("/path/to/file")
    assert str(error) == "File not found: /path/to/file"
    assert error.file_path == "/path/to/file"
    assert error.error_code == ErrorCode.FILE_NOT_FOUND

    # Test with Path object
    path = Path("/path/to/file")
    error = TorrentFileNotFoundError(path)
    assert str(error) == "File not found: /path/to/file"
    assert error.file_path == str(path)


def test_torrent_permission_error() -> None:
    """Test TorrentPermissionError exception."""
    # Test with string path
    error = TorrentPermissionError("/path/to/file", "read")
    assert (
        str(error)
        == "Permission denied for read on: /path/to/file (details: {'path': '/path/to/file', 'operation': 'read'})"
    )
    assert error.path == "/path/to/file"
    assert error.operation == "read"
    assert error.details == {"path": "/path/to/file", "operation": "read"}

    # Test with Path object
    path = Path("/path/to/file")
    error = TorrentPermissionError(path, "write")
    assert (
        str(error)
        == "Permission denied for write on: /path/to/file (details: {'path': '/path/to/file', 'operation': 'write'})"
    )
    assert error.path == str(path)
    assert error.operation == "write"


def test_invalid_metadata_error() -> None:
    """Test InvalidMetadataError exception."""
    # Test without details
    error = InvalidMetadataError("bad metadata")
    assert str(error) == "Invalid metadata: bad metadata"
    assert error.error_code == ErrorCode.ERROR
    assert error.details == {}

    # Test with details
    details = {"field": "source", "value": "invalid"}
    error = InvalidMetadataError("bad metadata", details)
    assert error.details == details


def test_max_failures_exceeded_error() -> None:
    """Test MaxFailuresExceededError exception."""
    # Test without failed items
    error = MaxFailuresExceededError(5)
    assert (
        str(error)
        == "Stopping after 5 failures (details: {'failures': 5, 'failed_items': []})"
    )
    assert error.error_code == ErrorCode.MAX_FAILURES_EXCEEDED
    assert error.details == {"failures": 5, "failed_items": []}

    # Test with failed items
    failed_items = ["/path1", "/path2"]
    error = MaxFailuresExceededError(2, failed_items)
    assert (
        str(error)
        == "Stopping after 2 failures (details: {'failures': 2, 'failed_items': ['/path1', '/path2']})"
    )
    assert error.details == {"failures": 2, "failed_items": failed_items}


def test_no_subdirectories_error() -> None:
    """Test NoSubdirectoriesError exception."""
    # Test with string path
    error = NoSubdirectoriesError("/path/to/dir")
    assert (
        str(error)
        == "No subdirectories found in: /path/to/dir (details: {'directory': '/path/to/dir'})"
    )
    assert error.directory == "/path/to/dir"
    assert error.error_code == ErrorCode.NO_SUBDIRECTORIES
    assert error.details == {"directory": "/path/to/dir"}

    # Test with Path object
    path = Path("/path/to/dir")
    error = NoSubdirectoriesError(path)
    assert (
        str(error)
        == "No subdirectories found in: /path/to/dir (details: {'directory': '/path/to/dir'})"
    )
    assert error.directory == str(path)


def test_directory_not_found_error() -> None:
    """Test DirectoryNotFoundError exception."""
    # Test with string path
    error = DirectoryNotFoundError("/path/to/dir")
    assert (
        str(error)
        == "Directory not found: /path/to/dir (details: {'directory': '/path/to/dir'})"
    )
    assert error.directory == "/path/to/dir"
    assert error.error_code == ErrorCode.DIRECTORY_NOT_FOUND
    assert error.details == {"directory": "/path/to/dir"}

    # Test with Path object
    path = Path("/path/to/dir")
    error = DirectoryNotFoundError(path)
    assert (
        str(error)
        == "Directory not found: /path/to/dir (details: {'directory': '/path/to/dir'})"
    )
    assert error.directory == str(path)


def test_invalid_directory_structure_error() -> None:
    """Test InvalidDirectoryStructureError exception."""
    # Test with string path
    error = InvalidDirectoryStructureError("/path/to/dir", "missing required files")
    assert (
        str(error)
        == "Invalid directory structure in /path/to/dir: missing required files (details: {'directory': '/path/to/dir', 'reason': 'missing required files'})"
    )
    assert error.directory == "/path/to/dir"
    assert error.reason == "missing required files"
    assert error.details == {
        "directory": "/path/to/dir",
        "reason": "missing required files",
    }

    # Test with Path object
    path = Path("/path/to/dir")
    error = InvalidDirectoryStructureError(path, "invalid layout")
    assert (
        str(error)
        == "Invalid directory structure in /path/to/dir: invalid layout (details: {'directory': '/path/to/dir', 'reason': 'invalid layout'})"
    )
    assert error.directory == str(path)
    assert error.reason == "invalid layout"


def test_manifest_error() -> None:
    """Test ManifestError exception."""
    # Test without details
    error = ManifestError("manifest error")
    assert str(error) == "manifest error"
    assert error.error_code == ErrorCode.ERROR
    assert error.details == {}

    # Test with details
    details = {"file": "manifest.csv", "line": 10}
    error = ManifestError("manifest error", details)
    assert error.details == details


def test_piece_size_error() -> None:
    """Test PieceSizeError exception."""
    # Test without details
    error = PieceSizeError("invalid piece size")
    assert str(error) == "Piece size error: invalid piece size"
    assert error.error_code == ErrorCode.ERROR
    assert error.details == {}

    # Test with details
    details = {"min": "16K", "max": "32M"}
    error = PieceSizeError("invalid piece size", details)
    assert (
        str(error)
        == "Piece size error: invalid piece size (details: {'min': '16K', 'max': '32M'})"
    )
    assert error.details == details


def test_missing_torrent_files_error() -> None:
    """Test MissingTorrentFilesError exception."""
    missing_files = ["/path/to/file1.torrent", "/path/to/file2.torrent"]
    error = MissingTorrentFilesError(missing_files)
    assert (
        str(error)
        == "Found 2 missing torrent files (details: {'missing_files': ['/path/to/file1.torrent', '/path/to/file2.torrent']})"
    )
    assert error.error_code == ErrorCode.MISSING_TORRENT_FILES
    assert error.details == {"missing_files": missing_files}


def test_invalid_tracker_url_error() -> None:
    """Test InvalidTrackerURLError exception."""
    error = InvalidTrackerURLError("http://bad.url", "invalid scheme")
    assert (
        str(error)
        == "Invalid tracker URL (http://bad.url): invalid scheme (details: {'url': 'http://bad.url', 'reason': 'invalid scheme'})"
    )
    assert error.error_code == ErrorCode.INVALID_TRACKER_URL
    assert error.details == {"url": "http://bad.url", "reason": "invalid scheme"}


def test_batch_processing_error() -> None:
    """Test BatchProcessingError exception."""
    # Test without details
    inner_error = ValueError("test error")
    error = BatchProcessingError(inner_error)
    assert error.error_code == ErrorCode.BATCH_PROCESSING_ERROR
    assert error.details == {"error": str(inner_error)}
    assert "Batch processing failed: test error" in str(error)
    assert "details: {'error': 'test error'}" in str(error)

    # Test with details
    details = {"stage": "processing", "file": "test.torrent"}
    error = BatchProcessingError(inner_error, details)
    assert error.error_code == ErrorCode.BATCH_PROCESSING_ERROR
    assert error.details == {
        "error": str(inner_error),
        "stage": "processing",
        "file": "test.torrent",
    }
    assert "Batch processing failed: test error" in str(error)
    assert all(
        detail in str(error)
        for detail in [
            "'error': 'test error'",
            "'stage': 'processing'",
            "'file': 'test.torrent'",
        ]
    )
