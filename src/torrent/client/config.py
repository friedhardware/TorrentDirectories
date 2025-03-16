"""Configuration for the torrent client."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ClientConfig:
    """Configuration for the torrent client."""

    torrent_dir: Path
    """Directory containing torrent files to seed."""

    data_dir: Optional[Path] = None
    """Directory containing the actual data files. If None, uses torrent_dir."""

    port: int = 6881
    """Port to listen on for peer connections."""

    max_upload_rate: int = 0
    """Maximum upload rate in bytes per second. 0 means unlimited."""

    max_download_rate: int = 0
    """Maximum download rate in bytes per second. 0 means unlimited."""

    max_connections: int = 200
    """Maximum number of peer connections."""

    check_interval: int = 60
    """Interval in seconds to check for new torrents."""

    auto_restart: bool = False
    """Whether to automatically restart the batch process."""

    batch_config: Optional[dict] = None
    """Configuration for the batch process if auto_restart is enabled."""

    # Auto-restart specific settings
    batch_check_interval: int = 300
    """Interval in seconds to check for new directories to process."""

    batch_max_failures: int = 0
    """Maximum number of failures before stopping the batch process."""

    batch_clean: bool = True
    """Whether to clean the manifest on each batch run."""

    batch_force: bool = True
    """Whether to force recreation of torrents on each batch run."""

    batch_dry_run: bool = False
    """Whether to show what would be done without making changes."""

    # Web interface settings
    web_enabled: bool = False
    """Whether to enable the web interface."""

    web_port: int = 5000
    """Port to listen on for the web interface."""
