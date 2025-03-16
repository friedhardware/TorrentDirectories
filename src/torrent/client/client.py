"""Torrent client implementation using libtorrent."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Set

import libtorrent as lt

from ..utils import DEFAULT_MAX_PIECE_SIZE, DEFAULT_MIN_PIECE_SIZE
from ..web.server import WebInterface
from .config import ClientConfig

logger = logging.getLogger(__name__)


class TorrentClient:
    """A torrent client that can seed torrents and monitor for new ones."""

    def __init__(self, config: ClientConfig):
        """Initialize the torrent client.

        Args:
            config: Client configuration
        """
        self.config = config
        self.session = lt.session()
        self.torrents: Dict[str, lt.torrent_handle] = {}
        self._setup_session()

        # Initialize web interface if enabled
        self.web_interface: Optional[WebInterface] = None
        if config.web_enabled:
            self.web_interface = WebInterface(port=config.web_port)
            self.web_interface.set_batch_handlers(
                on_start=self._start_batch_process, on_stop=self._stop_batch_process
            )

        # Auto-restart state
        self.last_batch_run: float = 0
        self.batch_running: bool = False
        self.next_batch_check: float = 0
        self.auto_restart_enabled: bool = config.auto_restart

    def _setup_session(self) -> None:
        """Configure the libtorrent session."""
        # Set up session settings
        settings = {
            "listen_interfaces": f"0.0.0.0:{self.config.port}",
            "upload_rate_limit": (
                self.config.max_upload_rate * 1024 if self.config.max_upload_rate else 0
            ),
            "download_rate_limit": (
                self.config.max_download_rate * 1024
                if self.config.max_download_rate
                else 0
            ),
            "connections_limit": (
                self.config.max_connections if self.config.max_connections else -1
            ),
        }
        self.session.apply_settings(settings)

    async def start(self) -> None:
        """Start the client."""
        # Start web interface if enabled
        if self.web_interface:
            self.web_interface.start()

        # Start monitoring for new torrents
        try:
            while True:
                await self._check_torrents()
                await asyncio.sleep(self.config.check_interval)
        except asyncio.CancelledError:
            logger.info("Client stopping...")
            await self.stop()

    async def stop(self) -> None:
        """Stop the client."""
        # Stop web interface if enabled
        if self.web_interface:
            self.web_interface.stop()

        # Remove all torrents
        for handle in self.torrents.values():
            self.session.remove_torrent(handle)
        self.torrents.clear()

    async def _load_torrents(self) -> None:
        """Load all torrents from the torrent directory."""
        for torrent_file in self.config.torrent_dir.glob("*.torrent"):
            try:
                await self.add_torrent(torrent_file)
            except Exception as e:
                logger.error(f"Failed to load torrent {torrent_file}: {e}")
                if self.web_interface:
                    self.web_interface.add_error(
                        f"Failed to load torrent {torrent_file.name}: {e}"
                    )

    async def add_torrent(self, torrent_path: Path) -> None:
        """Add a torrent to the client.

        Args:
            torrent_path: Path to the torrent file
        """
        if str(torrent_path) in self.torrents:
            logger.info(f"Torrent {torrent_path} already loaded")
            return

        try:
            # Create torrent info
            info = lt.torrent_info(str(torrent_path))

            # Set up torrent parameters
            params = {
                "ti": info,
                "save_path": str(self.config.data_dir or self.config.torrent_dir),
            }

            # Add torrent to session
            handle = self.session.add_torrent(params)
            self.torrents[str(torrent_path)] = handle

            # Update web interface if enabled
            if self.web_interface:
                self.web_interface.update_torrents(self.torrents)

            logger.info(f"Added torrent: {torrent_path.name}")

        except Exception as e:
            logger.error(f"Failed to add torrent {torrent_path}: {e}")
            if self.web_interface:
                self.web_interface.add_error(
                    f"Failed to add torrent {torrent_path.name}: {e}"
                )
            raise

    async def _check_torrents(self) -> None:
        """Check for new torrents and update status."""
        # Update web interface if enabled
        if self.web_interface:
            self.web_interface.update_torrents(self.torrents)

        # Check for new torrents
        if self.config.watch_dir:
            await self._scan_watch_dir()

        # Update status for all torrents
        for handle in self.torrents.values():
            status = handle.status()
            logger.debug(f"Torrent {handle.name()} status: {status.state_str}")

    async def _monitor_torrents(self) -> None:
        """Monitor the torrent directory for new torrents."""
        known_torrents: Set[str] = set()

        while True:
            try:
                # Get current torrent files
                current_torrents = {
                    str(p) for p in self.config.torrent_dir.glob("*.torrent")
                }

                # Find new torrents
                new_torrents = current_torrents - known_torrents

                # Add new torrents
                for torrent_path in new_torrents:
                    await self.add_torrent(Path(torrent_path))

                # Update known torrents
                known_torrents = current_torrents

                # Update web interface if enabled
                if self.web_interface:
                    self.web_interface.update_torrents(self.torrents)
                    self.web_interface.update_batch_status(
                        is_running=self.batch_running,
                        last_run=int(self.last_batch_run),
                        next_check=int(self.next_batch_check),
                        message=(
                            "Monitoring for new torrents"
                            if not self.batch_running
                            else None
                        ),
                    )

                # Check torrent status
                for torrent_path, handle in self.torrents.items():
                    status = handle.status()
                    if status.is_seeding:
                        logger.debug(f"Seeding: {Path(torrent_path).name}")
                    elif status.is_downloading:
                        logger.debug(f"Downloading: {Path(torrent_path).name}")

                # Handle auto-restart if enabled
                if self.auto_restart_enabled and self.config.batch_config:
                    await self._check_auto_restart()

                # Wait before next check
                await asyncio.sleep(self.config.check_interval)

            except Exception as e:
                logger.error(f"Error in torrent monitor: {e}")
                if self.web_interface:
                    self.web_interface.add_error(f"Error in torrent monitor: {e}")
                await asyncio.sleep(self.config.check_interval)

    async def _check_auto_restart(self) -> None:
        """Check if we should restart the batch process."""
        if self.batch_running:
            return

        # Check if we've waited long enough since last run
        current_time = time.time()
        if current_time - self.last_batch_run < self.config.batch_check_interval:
            self.next_batch_check = (
                self.last_batch_run + self.config.batch_check_interval
            )
            return

        # Check if we have any new torrents to process
        if not any(handle.status().is_seeding for handle in self.torrents.values()):
            await self._start_batch_process()

    async def _start_batch_process(self) -> None:
        """Start the batch process."""
        if self.batch_running:
            return

        current_time = int(time.time())
        self.batch_running = True
        self.batch_config = {
            "is_running": True,
            "last_run": current_time,
            "next_check": current_time + int(self.config.check_interval),
            "message": "Starting batch process",
            "success": False,
            "failure": False,
        }
        self._update_batch_status(self.batch_config)

    async def _stop_batch_process(self) -> None:
        """Stop the batch process."""
        if not self.batch_running:
            return

        current_time = int(time.time())
        self.batch_running = False
        self.batch_config = {
            "is_running": False,
            "last_run": current_time,
            "next_check": current_time + int(self.config.check_interval),
            "message": "Batch process stopped",
            "success": False,
            "failure": False,
        }
        self._update_batch_status(self.batch_config)

    def _update_batch_status(self, status: Optional[Dict[str, Any]]) -> None:
        """Update batch status in web interface."""
        if self.web_interface and status is not None:
            last_run = status.get("last_run", 0)
            next_check = status.get("next_check", 0)
            self.web_interface.update_batch_status(
                is_running=status.get("is_running", False),
                last_run=int(last_run) if isinstance(last_run, (int, float)) else 0,
                next_check=(
                    int(next_check) if isinstance(next_check, (int, float)) else 0
                ),
                message=status.get("message"),
                success=status.get("success", False),
                failure=status.get("failure", False),
            )

    def _update_batch_process(self) -> None:
        """Update batch process status."""
        if not self.batch_running:
            return

        current_time = int(time.time())
        self.batch_config = {
            "is_running": True,
            "last_run": current_time,
            "next_check": current_time + int(self.config.check_interval),
            "message": "Batch process running",
            "success": False,
            "failure": False,
        }
        self._update_batch_status(self.batch_config)

    def _batch_process_success(self) -> None:
        """Handle batch process success."""
        current_time = int(time.time())
        self.batch_config = {
            "is_running": False,
            "last_run": current_time,
            "next_check": current_time + int(self.config.check_interval),
            "message": "Batch process completed successfully",
            "success": True,
            "failure": False,
        }
        self._update_batch_status(self.batch_config)

    def _batch_process_failure(self, error: str) -> None:
        """Handle batch process failure."""
        current_time = int(time.time())
        self.batch_config = {
            "is_running": False,
            "last_run": current_time,
            "next_check": current_time + int(self.config.check_interval),
            "message": f"Batch process failed: {error}",
            "success": False,
            "failure": True,
        }
        self._update_batch_status(self.batch_config)


async def run_client(
    torrent_dir: str,
    data_dir: Optional[str] = None,
    port: int = 6881,
    max_upload_rate: int = 0,
    max_download_rate: int = 0,
    max_connections: int = 50,
    check_interval: int = 60,
    auto_restart: bool = False,
    batch_config: Optional[dict] = None,
    web: bool = False,
    web_port: int = 5000,
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
        auto_restart: Whether to automatically restart the batch process
        batch_config: Configuration for batch processing
        web: Whether to enable the web interface
        web_port: Port for the web interface

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
            auto_restart=auto_restart,
            batch_config=batch_config,
            web_enabled=web,
            web_port=web_port,
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
