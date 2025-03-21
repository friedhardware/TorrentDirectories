"""
Base exceptions for the torrent library.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ErrorCode(Enum):
    """Error codes for the torrent module."""

    SUCCESS = 0  # Operation completed successfully
    ERROR = 1  # General error condition
    USAGE_ERROR = 2  # Command line usage error

    # File system errors
    NO_DATA = 10  # File or directory contains no data
    EMPTY_DIRECTORY = 11  # Directory is empty
    FILE_EXISTS = 12  # File already exists
    FILE_NOT_FOUND = 13  # File not found

    # Processing errors
    INVALID_CONFIG = 20  # Invalid configuration
    CREATION_ERROR = 21  # Error creating torrent file
    TORRENT_CREATION_ERROR = 22  # Error during torrent creation
    BATCH_PROCESSING_ERROR = 23  # Error during batch processing
    MAX_FAILURES_EXCEEDED = 24  # Maximum failures exceeded in batch mode
    INVALID_TRACKER_URL = 25  # Invalid tracker URL
    INVALID_METADATA = 26  # Invalid metadata
    INVALID_PIECE_SIZE = 27  # Invalid piece size

    # Directory-related errors
    NO_SUBDIRECTORIES = 5
    MISSING_TORRENT_FILES = 6
    DIRECTORY_NOT_FOUND = 8


class TorrentError(Exception):
    """Base class for all torrent exceptions."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.ERROR,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            error_code: The error code.
            details: Additional details about the error.
        """
        super().__init__(message)
        self._message = message  # Store message explicitly for __str__
        self.error_code = error_code
        self.details = {}
        if details is not None:
            self.details.update(details)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self._message} (details: {self.details})"
        return self._message

    @property
    def message(self) -> str:
        """Get the error message.

        Returns:
            str: The error message.
        """
        return self._message


class NoDataError(TorrentError):
    """Raised when a file or directory contains no data."""

    def __init__(self, path: str, is_directory: bool = False) -> None:
        """Initialize the exception.

        Args:
            path: The path to the file or directory.
            is_directory: Whether the path is a directory.
        """
        message = (
            f"Directory {path} contains no data"
            if is_directory
            else f"File {path} contains no data"
        )
        super().__init__(message, ErrorCode.NO_DATA)


class OutputFileExistsError(TorrentError):
    """Raised when the output file already exists."""

    def __init__(self, path: str) -> None:
        """Initialize the exception.

        Args:
            path: The path to the file.
        """
        super().__init__(
            f"Output file already exists: {path}",
            ErrorCode.FILE_EXISTS,
        )


class TorrentCreationError(TorrentError):
    """Error during torrent creation."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """Initialize the error.

        Args:
            message: The error message.
            details: Additional details about the error.
        """
        super().__init__(message, ErrorCode.TORRENT_CREATION_ERROR, details)


class InvalidConfigError(TorrentError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
        """
        super().__init__(
            f"Invalid configuration: {message}",
            ErrorCode.INVALID_CONFIG,
        )


class TorrentVerificationError(TorrentError):
    """Error during torrent verification."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """Initialize the error.

        Args:
            message: The error message.
            details: Additional details about the error.
        """
        super().__init__(message, ErrorCode.TORRENT_CREATION_ERROR, details)


# File-related exceptions
class TorrentFileNotFoundError(TorrentError):
    """Raised when a file cannot be found."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = str(file_path)
        super().__init__(
            f"File not found: {self.file_path}",
            ErrorCode.FILE_NOT_FOUND,
        )


class TorrentPermissionError(TorrentError):
    """Raised when permission is denied for a file operation."""

    def __init__(self, path: str | Path, operation: str) -> None:
        self.path = str(path)
        self.operation = operation
        super().__init__(
            f"Permission denied for {operation} on: {self.path}",
            ErrorCode.ERROR,
            {"path": self.path, "operation": operation},
        )


class InvalidMetadataError(TorrentError):
    """Raised when torrent metadata is invalid."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(f"Invalid metadata: {message}", ErrorCode.ERROR, details)


class MaxFailuresExceededError(TorrentError):
    """Raised when the maximum allowed failures is exceeded."""

    def __init__(self, failures: int, failed_items: Optional[list[str]] = None) -> None:
        super().__init__(
            f"Stopping after {failures} failures",
            ErrorCode.MAX_FAILURES_EXCEEDED,
            {"failures": failures, "failed_items": failed_items or []},
        )


# Directory-related exceptions
class NoSubdirectoriesError(TorrentError):
    """Raised when no subdirectories are found in batch mode."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = str(directory)
        super().__init__(
            f"No subdirectories found in: {self.directory}",
            ErrorCode.NO_SUBDIRECTORIES,
            {"directory": self.directory},
        )


class DirectoryNotFoundError(TorrentError):
    """Raised when a directory cannot be found."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = str(directory)
        super().__init__(
            f"Directory not found: {self.directory}",
            ErrorCode.DIRECTORY_NOT_FOUND,
            {"directory": self.directory},
        )


class InvalidDirectoryStructureError(TorrentError):
    """Raised when directory structure is invalid for the operation."""

    def __init__(self, directory: str | Path, reason: str) -> None:
        self.directory = str(directory)
        self.reason = reason
        super().__init__(
            f"Invalid directory structure in {self.directory}: {reason}",
            ErrorCode.ERROR,
            {"directory": self.directory, "reason": reason},
        )


# Processing exceptions
class ManifestError(TorrentError):
    """Raised when there's an error with the manifest file."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """Initialize the error.

        Args:
            message: The error message.
            details: Additional details about the error.
        """
        super().__init__(message, ErrorCode.ERROR, details)


class PieceSizeError(TorrentError):
    """Raised when there's an error with piece size calculations."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(f"Piece size error: {message}", ErrorCode.ERROR, details)


class MissingTorrentFilesError(TorrentError):
    """Raised when torrent files listed in manifest are missing."""

    def __init__(self, missing_files: list[str]) -> None:
        self.missing_files = missing_files
        super().__init__(
            f"Found {len(missing_files)} missing torrent files",
            ErrorCode.MISSING_TORRENT_FILES,
            {"missing_files": missing_files},
        )


# Configuration exceptions
class InvalidTrackerURLError(TorrentError):
    """Raised when tracker URL is invalid."""

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(
            f"Invalid tracker URL ({url}): {reason}",
            ErrorCode.INVALID_TRACKER_URL,
            {"url": url, "reason": reason},
        )


# Processing exceptions
class BatchProcessingError(TorrentError):
    """Raised when batch processing encounters an error."""

    def __init__(
        self, error: Exception, details: Optional[dict[str, Any]] = None
    ) -> None:
        """Initialize the error.

        Args:
            error: The original exception that caused this error.
            details: Additional details about the error.
        """
        error_details = details or {}
        error_details["error"] = str(error)
        super().__init__(
            f"Batch processing failed: {error}",
            ErrorCode.BATCH_PROCESSING_ERROR,
            error_details,
        )
