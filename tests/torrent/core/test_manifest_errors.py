"""Tests for manifest error handling."""

from torrent.core.manifest.exceptions import ManifestError
from torrent.errors.exceptions import ErrorCode


def test_manifest_error_creation():
    """Test creating a manifest error with details."""
    error = ManifestError("Test error", details={"file": "test.txt"})
    assert str(error) == "Test error (details: {'file': 'test.txt'})"
    assert error.details == {"file": "test.txt"}
    assert error.error_code == ErrorCode.ERROR


def test_manifest_error_without_details():
    """Test creating a manifest error without details."""
    error = ManifestError("Simple error")
    assert str(error) == "Simple error"
    assert error.details == {}
    assert error.error_code == ErrorCode.ERROR


def test_manifest_error_with_empty_details():
    """Test creating a manifest error with empty details."""
    error = ManifestError("Empty details", details={})
    assert str(error) == "Empty details"
    assert error.details == {}
    assert error.error_code == ErrorCode.ERROR


def test_manifest_error_with_nested_details():
    """Test creating a manifest error with nested details."""
    details = {"file": "test.txt", "metadata": {"size": 1024, "type": "file"}}
    error = ManifestError("Complex error", details=details)
    assert (
        str(error)
        == "Complex error (details: {'file': 'test.txt', 'metadata': {'size': 1024, 'type': 'file'}})"
    )
    assert error.details == details
    assert error.error_code == ErrorCode.ERROR
