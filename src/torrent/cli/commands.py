"""
Command handlers for CLI operations.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from ..manifest import ManifestError, ManifestManager
from ..torrent_creator import TorrentCreator
from .config import TorrentConfig

logger = logging.getLogger(__name__)


def process_single(
    path: str,
    tracker: str,
    output: Optional[str] = None,
    config: Optional[TorrentConfig] = None,
    force: bool = False,
) -> int:
    """Create a torrent file from a single file or directory.

    Args:
        path: Path to process
        tracker: Tracker URL to use
        output: Optional custom output path
        config: Optional torrent configuration
        force: Whether to overwrite existing torrent file

    Returns:
        0 on success, 1 on error
    """
    try:
        # Remove the os.path.exists check since pathvalidate will handle invalid paths
        if output and Path(output).exists() and not force:
            logger.error("Output file already exists. Use --force to overwrite.")
            return 1

        # Create torrent
        creator = TorrentCreator(tracker, config)
        torrent_path = creator.create(path, output or f"{path}.torrent")

        logger.info(f"\nTorrent created successfully: {torrent_path}")
        return 0

    except Exception as e:
        logger.error(f"Error creating torrent: {e}")
        return 1


def process_batch(
    directory: str,
    tracker: str,
    output_dir: str = "torrents/",
    config: Optional[TorrentConfig] = None,
    force: bool = False,
    clean: bool = False,
    max_failures: int = 0,
) -> int:
    """Process all subdirectories in a directory, creating torrents for each.

    Args:
        directory: Directory containing subdirectories to process
        tracker: Tracker URL to use for all torrents
        output_dir: Directory to store torrent files in
        config: Optional torrent configuration
        force: Whether to overwrite existing torrent files
        clean: Whether to clean the manifest before processing
        max_failures: Maximum number of failures before stopping (0 for unlimited)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Get list of subdirectories
        subdirs = [
            d
            for d in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, d))
        ]
        if not subdirs:
            logger.error("No subdirectories found to process")
            return 1

        # Create manifest manager
        manifest = ManifestManager(output_dir)

        # Clean manifest if requested
        if clean:
            missing = manifest.get_missing_torrents()
            if missing:
                logger.warning(f"\nFound {len(missing)} missing torrent files:")
                for path in missing:
                    logger.warning(f"  {path}")
            manifest.clean_manifest(output_dir)

        # Process each subdirectory
        failures = 0
        logger.info(f"\nProcessing {len(subdirs)} directories:")

        for subdir in sorted(subdirs):
            try:
                path = os.path.join(directory, subdir)
                torrent_path = os.path.join(output_dir, f"{subdir}.torrent")

                # Skip if torrent exists and not forcing
                if os.path.exists(torrent_path) and not force:
                    logger.info(f"  {subdir}: Skipped (already exists)")
                    continue

                # Create torrent
                creator = TorrentCreator(tracker, config)
                torrent_path = creator.create(path, torrent_path)
                manifest.add_entry(subdir, torrent_path)

                logger.info(f"  {subdir}: Created {torrent_path} ✓")

            except Exception as e:
                failures += 1
                logger.error(f"  {subdir}: Failed - {e}")

                if max_failures > 0 and failures >= max_failures:
                    logger.error("\nStopping due to too many failures")
                    return 1

        # Show summary if there were failures
        if failures > 0:
            logger.warning(f"\nCompleted with {failures} failures")
            return 1

        return 0

    except ManifestError as e:
        logger.error(f"Manifest error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        return 1


async def run_client(
    torrent_dir: str,
    data_dir: Optional[str] = None,
    port: int = 6881,
    max_upload_rate: int = 0,
    max_download_rate: int = 0,
    max_connections: int = 200,
    check_interval: int = 60,
    auto_restart: bool = False,
    batch_config: Optional[dict] = None,
    web: bool = False,
    web_port: int = 5000,
) -> int:
    """Run the torrent client.

    Args:
        torrent_dir: Directory containing torrent files
        data_dir: Directory containing data files (defaults to torrent_dir)
        port: Port to listen on
        max_upload_rate: Maximum upload rate in bytes/s (0 for unlimited)
        max_download_rate: Maximum download rate in bytes/s (0 for unlimited)
        max_connections: Maximum number of peer connections
        check_interval: Interval in seconds to check for new torrents
        auto_restart: Whether to automatically restart the batch process
        batch_config: Configuration for the batch process if auto_restart is enabled
        web: Whether to enable the web interface
        web_port: Port to listen on for the web interface

    Returns:
        0 on success, 1 on error
    """
    try:
        from ..client import ClientConfig, TorrentClient

        # Create client config
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

        # Keep the client running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping client...")
            await client.stop()
            return 0

    except Exception as e:
        logger.error(f"Error running client: {e}")
        return 1
