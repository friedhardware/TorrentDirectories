"""Custom exceptions for the torrent module."""

from __future__ import annotations


class TorrentError(Exception):
    """Base exception for torrent-related errors."""
    pass


class SecurityError(TorrentError):
    """Security-related errors."""
    pass


class ValidationError(TorrentError):
    """Validation-related errors."""
    pass


class FileSystemError(TorrentError):
    """File system operation errors."""
    pass


class ConfigError(TorrentError):
    """Configuration-related errors."""
    pass


class CreationError(TorrentError):
    """Torrent creation errors."""
    pass 