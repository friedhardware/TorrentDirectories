"""
Custom exceptions for the CLI.
"""

from __future__ import annotations

import click


class TorrentError(click.ClickException):
    """Base exception for torrent-related errors."""

    pass


class OutputFileExistsError(TorrentError):
    """Raised when an output file already exists and force is not set."""

    def __init__(self, output_path: str) -> None:
        super().__init__(
            f"Output file already exists: {output_path}\n" "Use --force to overwrite"
        )


class NoSubdirectoriesError(TorrentError):
    """Raised when no subdirectories are found to process."""

    def __init__(self, directory: str) -> None:
        super().__init__(f"No subdirectories found in {directory}")


class MissingTorrentFilesError(TorrentError):
    """Raised when the manifest contains entries for missing torrent files."""

    def __init__(self, missing_files: list[str]) -> None:
        super().__init__(
            f"Found {len(missing_files)} missing torrent files.\n"
            "Use --clean to remove invalid entries from manifest."
        )


class TorrentCreationError(TorrentError):
    """Raised when torrent creation fails."""

    def __init__(self, error: Exception) -> None:
        super().__init__(f"Error creating torrent: {error}")


class BatchProcessingError(TorrentError):
    """Raised when batch processing encounters an error."""

    def __init__(self, error: Exception) -> None:
        super().__init__(f"Error during batch processing: {error}")


class MaxFailuresExceededError(TorrentError):
    """Raised when the maximum allowed failures is exceeded."""

    def __init__(self, failures: int) -> None:
        super().__init__(f"Stopping after {failures} failures")


class FileIsEmptyError(Exception):
    """Raised when a file is empty and skip_empty_files is False."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        super().__init__(f"File {file_path} is empty (0 bytes)")
