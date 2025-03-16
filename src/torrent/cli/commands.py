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
from ..utils.config import TorrentConfig
from ..utils.file_utils import format_size, get_total_size, list_files

logger = logging.getLogger(__name__)


def handle_dry_run(
    path: str,
    output: Optional[str],
    config: Optional[TorrentConfig],
    is_batch: bool = False,
) -> None:
    """Handle the dry run logic for both single and batch processing."""
    logger.info("\nDry run mode - no changes will be made")
    logger.info(f"Would create torrent from: {path}")
    if output:
        logger.info(f"Would save to: {output}")

    if is_batch:
        # Get subdirectories to process
        subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        logger.info(f"\nWould process {len(subdirs)} directories:")
        for d in sorted(subdirs):
            logger.info(f"  {d}")
    else:
        # Handle single file/directory dry run
        files = list_files(
            path,
            skip_hidden=config.skip_hidden if config else True,
            skip_system=config.skip_system_files if config else True,
        )
        total_size = get_total_size([os.path.join(path, f) for f in files])
        logger.info(f"\nWould include {len(files)} files ({format_size(total_size)}):")
        for f in files:
            logger.info(f"  {f}")


def process_single(
    path: str,
    tracker_url: str,
    output: Optional[str] = None,
    config: Optional[TorrentConfig] = None,
    dry_run: bool = False,
    force: bool = False,
) -> int:
    """
    Create a torrent file from a single file or directory.

    Args:
        path: Path to process
        tracker_url: Tracker URL to use
        output: Optional custom output path
        config: Optional torrent configuration
        dry_run: Whether to show what would be done without making changes
        force: Whether to overwrite existing torrent file

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Check if output file exists
        if output and os.path.exists(output) and not force:
            logger.error(f"Output file already exists: {output}")
            logger.error("Use --force to overwrite")
            return 1

        torrent_creator = TorrentCreator(tracker_url, config)

        if dry_run:
            handle_dry_run(path, output, config)
            return 0

        # Actually create the torrent
        output_path = (
            output if output is not None else f"{os.path.basename(path)}.torrent"
        )
        torrent_path = torrent_creator.create(path, output_path)
        logger.info(f"\nTorrent created successfully: {torrent_path}")
        return 0

    except (ValueError, OSError) as e:
        logger.error(f"Error creating torrent: {e}")
        return 1


def process_batch(
    directory: str,
    tracker_url: str,
    config: Optional[TorrentConfig] = None,
    output_dir: str = "torrents/",
    dry_run: bool = False,
    clean: bool = False,
    force: bool = False,
    max_failures: int = 0,
) -> int:
    """
    Process all subdirectories in a parent directory.

    Args:
        directory: Parent directory to process
        tracker_url: Tracker URL to use
        config: Optional torrent configuration
        output_dir: Directory to store torrent files and manifest (defaults to 'torrents/')
        dry_run: Whether to show what would be done without making changes
        clean: Whether to clean the manifest
        force: Whether to overwrite existing torrent files
        max_failures: Maximum allowed failures before stopping

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Create output directory if not dry run
        if not dry_run:
            os.makedirs(output_dir, exist_ok=True)

        manifest = ManifestManager(output_dir)
        torrent_creator = TorrentCreator(tracker_url, config)

        # Check for missing torrent files
        missing = manifest.get_missing_torrents()
        if missing and not clean:
            logger.error(
                "\nFound missing torrent files that are listed in the manifest:"
            )
            for path in sorted(missing):
                logger.error(f"  {path}")
            logger.error("\nRun with --clean to remove invalid entries from manifest")
            return 1

        # Handle manifest cleaning if requested
        if clean and missing:
            logger.warning("\nFound missing torrent files:")
            for path in sorted(missing):
                logger.warning(f"  {path}")

            if not dry_run:
                manifest.clean_manifest(directory)
                logger.info(f"\nRemoved {len(missing)} invalid entries from manifest")
            else:
                logger.info("\nWould remove invalid entries from manifest")

        # Get subdirectories to process
        subdirs = [
            d
            for d in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, d))
        ]

        if not subdirs:
            logger.error(f"No subdirectories found in {directory}")
            return 1

        if dry_run:
            handle_dry_run(directory, output_dir, config, is_batch=True)
            return 0

        # Actually process directories
        logger.info(f"\nProcessing {len(subdirs)} directories:")
        failures = 0

        for subdir in sorted(subdirs):
            full_path = os.path.join(directory, subdir)

            # Skip if already processed and not forcing
            if manifest.is_directory_processed(full_path) and not force:
                logger.info(f"  {subdir}: Already processed ✓")
                continue

            # Create torrent and add to manifest
            try:
                # Set output path for the torrent file
                torrent_file_path = os.path.join(output_dir, f"{subdir}.torrent")
                torrent_path = torrent_creator.create(full_path, torrent_file_path)
                manifest.add_entry(full_path, torrent_path)
                logger.info(f"  {subdir}: Created {torrent_path} ✓")
            except Exception as e:
                logger.error(f"  {subdir}: Failed - {e}")
                failures += 1
                if max_failures > 0 and failures >= max_failures:
                    logger.error(f"\nStopping after {failures} failures")
                    return 1

        if failures > 0:
            logger.warning(f"\nCompleted with {failures} failures")
            return 1

        return 0

    except (ManifestError, ValueError, OSError) as e:
        logger.error(f"Error during batch processing: {e}")
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
