"""
Exceptions for the manifest module.
"""

from __future__ import annotations

from torrent.errors.exceptions import TorrentError


# Processing exceptions
class ManifestError(TorrentError):
    """Raised when there's an error with the manifest file."""

    pass


class ManifestCacheError(ManifestError):
    """Exception raised for manifest cache errors."""

    pass
