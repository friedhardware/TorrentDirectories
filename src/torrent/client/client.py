"""
BitTorrent client implementation.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

import libtorrent

from ..exceptions import ClientError
from ..utils.context import secure_temp_environment
from .config import ClientConfig

logger = logging.getLogger(__name__)


class TorrentClient:
    """BitTorrent client implementation."""

    def __init__(self, config: ClientConfig) -> None:
        """Initialize the client."""
        self.config = config
        self.session = libtorrent.session()
        self.running = False
        self.torrents: dict[str, libtorrent.torrent_handle] = {}

    async def start(self) -> None:
        """Start the client."""
        if self.running:
            return

        # Configure session
        self.session.listen_port(self.config.port)
        self.session.upload_rate_limit(self.config.max_upload_rate)
        self.session.download_rate_limit(self.config.max_download_rate)
        self.session.max_connections(self.config.max_connections)

        # Start background tasks
        self.running = True
        asyncio.create_task(self._monitor_torrents())

    async def stop(self) -> None:
        """Stop the client."""
        if not self.running:
            return

        self.running = False
        for handle in self.torrents.values():
            handle.pause()
        self.session.pause()

    async def _monitor_torrents(self) -> None:
        """Monitor the torrent directory for new torrents."""
        while self.running:
            try:
                # List torrent files
                torrent_files = [
                    f
                    for f in os.listdir(self.config.torrent_dir)
                    if f.endswith(".torrent")
                ]

                # Add new torrents
                for file in torrent_files:
                    if file not in self.torrents:
                        await self._add_torrent(file)

                # Update status
                await self._update_status()

            except Exception as e:
                logger.error(f"Error monitoring torrents: {e}")

            await asyncio.sleep(self.config.check_interval)

    async def _add_torrent(self, file: str) -> None:
        """Add a torrent to the session."""
        try:
            # Load torrent file
            torrent_path = self.config.torrent_dir / file
            info = libtorrent.torrent_info(str(torrent_path))

            # Set save path
            save_path = self.config.data_dir or self.config.torrent_dir

            # Add to session
            handle = self.session.add_torrent(
                {
                    "ti": info,
                    "save_path": str(save_path),
                }
            )
            self.torrents[file] = handle

            logger.info(f"Added torrent: {file}")

        except Exception as e:
            logger.error(f"Error adding torrent {file}: {e}")

    async def _update_status(self) -> None:
        """Update torrent status."""
        for file, handle in self.torrents.items():
            try:
                status = handle.status()
                progress = status.progress * 100

                if status.is_seeding:
                    logger.info(f"{file}: Seeding")
                else:
                    logger.info(
                        f"{file}: {progress:.1f}% "
                        f"({format_size(status.download_rate)}/s)"
                    )

            except Exception as e:
                logger.error(f"Error updating status for {file}: {e}")


def format_size(size: int) -> str:
    """Format size in bytes to human readable string."""
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PiB"


async def run_client(
    torrent_dir: str,
    data_dir: Optional[str] = None,
    port: int = 6881,
    max_upload_rate: int = 0,
    max_download_rate: int = 0,
    max_connections: int = 50,
    check_interval: int = 60,
) -> int:
    """Run the torrent client.

    Args:
        torrent_dir: Directory containing torrent files
        data_dir: Directory to save downloaded files (defaults to torrent_dir)
        port: Port to listen on
        max_upload_rate: Maximum upload rate in bytes/s (0 for unlimited)
        max_download_rate: Maximum download rate in bytes/s (0 for unlimited)
        max_connections: Maximum number of connections
        check_interval: How often to check for new torrents (in seconds)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Create client configuration
        config = ClientConfig(
            torrent_dir=Path(torrent_dir),
            data_dir=Path(data_dir) if data_dir else None,
            port=port,
            max_upload_rate=max_upload_rate,
            max_download_rate=max_download_rate,
            max_connections=max_connections,
            check_interval=check_interval,
        )

        # Create and start client
        client = TorrentClient(config)
        await client.start()

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            await client.stop()

        return 0

    except Exception as e:
        logger.error(f"Client error: {e}")
        return 1
