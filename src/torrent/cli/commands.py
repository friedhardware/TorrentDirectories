"""
Command handlers for CLI operations.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import click

from ..manifest import ManifestManager
from ..torrent_creator import TorrentCreator
from ..utils.config import TorrentConfig
from ..utils.file_utils import format_size, get_total_size, list_files
from ..utils.logging_utils import log_and_echo, log_batch_progress
from .exceptions import (
    BatchProcessingError,
    FileIsEmptyError,
    MaxFailuresExceededError,
    MissingTorrentFilesError,
    NoSubdirectoriesError,
    OutputFileExistsError,
    TorrentCreationError,
)

logger = logging.getLogger(__name__)


def handle_dry_run(
    path: str,
    output: Optional[str],
    config: Optional[TorrentConfig],
    is_batch: bool = False,
) -> None:
    """Handle the dry run logic for both single and batch processing."""
    log_and_echo("\nDry run mode - no changes will be made")
    log_and_echo(f"Would create torrent from: {path}")

    if output:
        log_and_echo(f"Would save to: {output}")

    if is_batch:
        # Get subdirectories to process
        subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        if not subdirs:
            raise NoSubdirectoriesError(path)
        log_and_echo(f"\nWould process {len(subdirs)} directories:")
        for d in sorted(subdirs):
            log_and_echo(f"  {d}")
    else:
        # Handle single file/directory dry run
        if os.path.isfile(path):
            size = os.path.getsize(path)
            log_and_echo(f"File size: {format_size(size)}")
        else:
            total_size = get_total_size([path])
            log_and_echo(f"Directory size: {format_size(total_size)}")
            log_and_echo("\nFiles that would be included:")
            for f in sorted(list_files(path)):
                log_and_echo(f"  {f}")


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

    Raises:
        OutputFileExistsError: If output file exists and force is not set
        TorrentCreationError: If torrent creation fails
        FileIsEmptyError: If file is empty and skip_empty_files is False
    """
    try:
        # Check if output file exists
        if output and os.path.exists(output) and not force:
            raise OutputFileExistsError(output)

        # Create config if not provided
        if config is None:
            config = TorrentConfig(tracker_url=tracker_url)
        else:
            # Update tracker URL in existing config
            config.tracker_url = tracker_url

        torrent_creator = TorrentCreator(config)

        if dry_run:
            handle_dry_run(path, output, config)
            return 0

        # Actually create the torrent
        output_path = (
            output if output is not None else f"{os.path.basename(path)}.torrent"
        )
        torrent_path = torrent_creator.create(path, output_path)
        log_and_echo(f"\nTorrent created successfully: {torrent_path}")
        return 0

    except Exception as e:
        if isinstance(
            e, (OutputFileExistsError, TorrentCreationError, FileIsEmptyError)
        ):
            raise
        raise TorrentCreationError(e)


def process_batch(
    directory: str,
    tracker_url: str,
    config: Optional[TorrentConfig] = None,
    output_dir: str = "torrents/",
    dry_run: bool = False,
    force: bool = False,
    clean: bool = False,
    max_failures: int = 0,
) -> int:
    """
    Create torrent files for all subdirectories in a directory.

    Args:
        directory: Directory containing subdirectories to process
        tracker_url: Tracker URL to use
        config: Optional torrent configuration
        output_dir: Directory to store torrent files and manifest (defaults to 'torrents/')
        dry_run: Whether to show what would be done without making changes
        force: Whether to overwrite existing torrent files
        clean: Whether to clean manifest of missing torrent files
        max_failures: Maximum number of failures before stopping (0 for unlimited)

    Returns:
        Exit code (0 for success, non-zero for failure)

    Raises:
        NoSubdirectoriesError: If directory has no subdirectories
        MissingTorrentFilesError: If manifest has missing torrent files and clean is False
        MaxFailuresExceededError: If number of failures exceeds max_failures
        BatchProcessingError: If batch processing encounters an error
        FileIsEmptyError: If file is empty and skip_empty_files is False
    """
    try:
        # Create config if not provided
        if config is None:
            config = TorrentConfig(tracker_url=tracker_url)
        else:
            # Update tracker URL in existing config
            config.tracker_url = tracker_url

        torrent_creator = TorrentCreator(config)

        # Get subdirectories to process
        subdirs = [
            d
            for d in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, d))
        ]

        if not subdirs:
            raise NoSubdirectoriesError(directory)

        if dry_run:
            handle_dry_run(directory, None, config, is_batch=True)
            return 0

        # Create output directory and manifest manager
        os.makedirs(output_dir, exist_ok=True)
        manifest = ManifestManager(output_dir)

        # Check for missing torrent files
        missing = manifest.get_missing_torrents()
        if missing and not clean:
            raise MissingTorrentFilesError(list(missing))

        # Handle manifest cleaning
        if clean and missing:
            log_and_echo("\nFound missing torrent files:", level="warning")
            for path in sorted(missing):
                log_and_echo(f"  {path}", level="warning")

            manifest.clean_manifest()
            log_and_echo(f"\nRemoved {len(missing)} invalid entries from manifest")

        # Process each subdirectory
        failures = (
            0  # Counts non-empty failures or all failures if skip_empty_files is False
        )
        skipped = 0  # Counts empty files that were skipped

        with click.progressbar(subdirs, label="Processing directories") as bar:
            for subdir in bar:
                full_path = os.path.join(directory, subdir)

                # Skip if already processed and not forcing
                if not force and manifest.is_directory_processed(full_path):
                    log_batch_progress(subdir)
                    continue

                # Create torrent and add to manifest
                try:
                    # Set output path for the torrent file
                    torrent_file_path = os.path.join(output_dir, f"{subdir}.torrent")
                    try:
                        torrent_path = torrent_creator.create(
                            full_path, torrent_file_path
                        )
                        manifest.add_entry(full_path, torrent_path, force=force)
                        log_batch_progress(subdir, torrent_path)
                    except FileIsEmptyError as e:
                        if config.skip_empty_files:
                            log_and_echo(
                                f"  {subdir}: Skipping empty file", level="warning"
                            )
                            skipped += 1
                        else:
                            log_and_echo(f"  {subdir}: Failed - {e}", level="error")
                            failures += 1
                            if failures >= max_failures:
                                raise MaxFailuresExceededError(failures)
                except FileIsEmptyError as e:
                    # Handle empty file error in outer block too
                    if config.skip_empty_files:
                        log_and_echo(
                            f"  {subdir}: Skipping empty file", level="warning"
                        )
                        skipped += 1
                    else:
                        log_and_echo(f"  {subdir}: Failed - {e}", level="error")
                        failures += 1
                        if failures >= max_failures:
                            raise MaxFailuresExceededError(failures)
                except Exception as e:
                    log_and_echo(f"  {subdir}: Failed - {e}", level="error")
                    failures += 1
                    if failures >= max_failures:
                        raise MaxFailuresExceededError(failures)

        if failures > 0:
            log_and_echo(f"\nCompleted with {failures} failures", level="warning")
            return 1

        if skipped > 0:
            log_and_echo(f"\nSkipped {skipped} empty files", level="warning")

        return 0

    except Exception as e:
        if isinstance(
            e,
            (NoSubdirectoriesError, MissingTorrentFilesError, MaxFailuresExceededError),
        ):
            raise
        raise BatchProcessingError(e)
