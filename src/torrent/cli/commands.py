"""
Command handlers for CLI operations.
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Union

import click

from ..exceptions import ErrorCode, NoDataError, OutputFileExistsError, TorrentError
from ..manifest import ManifestManager
from ..torrent_creator import TorrentCreator
from ..utils.config import TorrentConfig
from ..utils.file_utils import (
    format_size,
    get_total_size,
    is_directory_empty,
    list_files,
)

logger = logging.getLogger(__name__)


def handle_dry_run(
    path: str,
    output: Optional[str],
    config: Optional[TorrentConfig],
    is_batch: bool = False,
    force: bool = False,
) -> None:
    """Handle the dry run logic for both single and batch processing.

    Args:
        path: Path to process (file, directory, or parent directory for batch)
        output: Output path for torrent file(s)
        config: Torrent configuration
        is_batch: Whether this is a batch operation
        force: Whether to overwrite existing files
    """
    if is_batch:
        # Handle batch processing dry run
        if not os.path.isdir(path):
            raise TorrentError(
                message=f"Path is not a directory: {path}",
                error_code=ErrorCode.DIRECTORY_NOT_FOUND,
            )

        click.echo(f"Would process directory: {path}")
        output_dir = output or os.path.join(path, "torrents")
        click.echo(f"Would save torrents to: {output_dir}")

        files = list_files(
            path,
            skip_hidden=config.skip_hidden if config else True,
            skip_system=config.skip_system_files if config else True,
        )
        if not files:
            click.echo("Warning: Directory is empty")
        else:
            total_size = get_total_size([path])
            click.echo(f"Total size: {format_size(total_size)}")
            click.echo(f"\nDirectories that would be processed ({len(files)} total):")
            for f in sorted(files):
                click.echo(f"  {f}")
    else:
        # Handle single file/directory dry run
        if not os.path.exists(path):
            raise TorrentError(
                message=f"Path does not exist: {path}",
                error_code=ErrorCode.FILE_NOT_FOUND,
            )

        click.echo(f"Would create torrent from: {path}")
        output_path = output or f"{path}.torrent"
        click.echo(f"Would save to: {output_path}")
        if os.path.exists(output_path):
            if force:
                click.echo("Would overwrite existing output file")
            else:
                click.echo(
                    "Note: Output file already exists (use --force to overwrite)"
                )

        if os.path.isfile(path):
            size = os.path.getsize(path)
            click.echo(f"File size: {format_size(size)}")
        else:
            files = list_files(
                path,
                skip_hidden=config.skip_hidden if config else True,
                skip_system=config.skip_system_files if config else True,
            )
            if not files:
                click.echo("Warning: Directory is empty")
            else:
                total_size = get_total_size([path])
                click.echo(f"Directory size: {format_size(total_size)}")
                click.echo(f"\nFiles that would be included ({len(files)} total):")
                for f in sorted(files):
                    file_size = os.path.getsize(os.path.join(path, f))
                    click.echo(f"  {f} ({format_size(file_size)})")

    # Show configuration that would be used
    if config:
        click.echo("\nConfiguration:")
        click.echo(f"  Private: {config.private}")
        click.echo(f"  Min piece size: {format_size(config.min_piece_size)}")
        click.echo(f"  Max piece size: {format_size(config.max_piece_size)}")
        if config.source:
            click.echo(f"  Source: {config.source}")
        if config.comment:
            click.echo(f"  Comment: {config.comment}")
        click.echo(f"  Skip hidden files: {config.skip_hidden}")
        click.echo(f"  Skip system files: {config.skip_system_files}")


def process_single(
    path: str,
    tracker_url: str,
    output: Optional[str] = None,
    config: Optional[TorrentConfig] = None,
    dry_run: bool = False,
    force: bool = False,
) -> Union[int, TorrentError]:
    """
    Create a torrent file from a single file or directory.

    Args:
        path: Path to file or directory
        tracker_url: Tracker URL to use
        output: Optional output path for torrent file
        config: Optional torrent configuration
        dry_run: Whether to show what would be done without making changes
        force: Whether to overwrite existing torrent files

    Returns:
        0 for success, TorrentError for failures
    """
    try:
        logger.debug("Starting process_single with path: %s", path)
        logger.info("Processing file: %s", path)
        logger.debug("Using tracker URL: %s", tracker_url)

        # Check if path exists
        if not os.path.exists(path):
            logger.error("Path does not exist: %s", path)
            return TorrentError(
                message=f"Path does not exist: {path}",
                error_code=ErrorCode.FILE_NOT_FOUND,
            )

        # Check if output file exists
        output_path = (
            output if output is not None else f"{os.path.basename(path)}.torrent"
        )
        logger.debug("Output path: %s", output_path)

        if os.path.exists(output_path):
            if not force:
                logger.warning("Output file already exists: %s", output_path)
                return TorrentError(
                    message=f"Output file already exists: {output_path}",
                    error_code=ErrorCode.FILE_EXISTS,
                )
            else:
                logger.debug(
                    "Force flag set, will overwrite existing file: %s", output_path
                )

        # Create config if not provided
        if config is None:
            logger.debug("Creating default config with tracker URL: %s", tracker_url)
            config = TorrentConfig(tracker_url=tracker_url)
        else:
            # Update tracker URL in existing config
            logger.debug("Updating tracker URL in existing config: %s", tracker_url)
            config.tracker_url = tracker_url

        if dry_run:
            logger.debug("Performing dry run")
            handle_dry_run(path, output, config, is_batch=False, force=force)
            return 0

        # If force is True and file exists, remove it first
        if force and os.path.exists(output_path):
            logger.debug("Removing existing file: %s", output_path)
            os.remove(output_path)

        logger.info("Creating torrent file...")
        torrent_creator = TorrentCreator(config)
        try:
            logger.debug(
                "Calling TorrentCreator.create with path: %s, output: %s",
                path,
                output_path,
            )
            torrent_path = torrent_creator.create(path, output_path)
            logger.debug("Torrent created successfully at: %s", torrent_path)
            click.echo(f"\nTorrent created successfully: {torrent_path}")
            return 0
        except OutputFileExistsError as e:
            logger.error("Output file exists: %s", e)
            click.echo(f"Error: {e}", err=True)
            return TorrentError(
                message=str(e),
                error_code=ErrorCode.FILE_EXISTS,
                details={"path": str(e)},
            )
        except Exception as e:
            logger.error("Failed to create torrent: %s", e)
            if isinstance(e, TorrentError):
                return e
            return TorrentError(
                message=str(e),
                error_code=ErrorCode.TORRENT_CREATION_ERROR,
                details={"error": str(e)},
            )

    except Exception as e:
        logger.error("Unexpected error: %s", e)
        if isinstance(e, TorrentError):
            return e
        return TorrentError(
            message=str(e),
            error_code=ErrorCode.TORRENT_CREATION_ERROR,
            details={"original_error": str(e)},
        )


def process_batch(
    parent_dir: str,
    tracker_url: str,
    output_dir: str = "torrents/",
    config: Optional[TorrentConfig] = None,
    dry_run: bool = False,
    force: bool = False,
    max_failures: int = 0,
    clean: bool = False,
) -> Union[int, TorrentError]:
    """
    Process all subdirectories in a parent directory.

    Args:
        parent_dir: Parent directory containing subdirectories to process
        tracker_url: Tracker URL to use
        output_dir: Output directory for torrent files
        config: Optional torrent configuration
        dry_run: Whether to show what would be done without making changes
        force: Whether to overwrite existing torrent files
        max_failures: Maximum allowed failures before stopping (-1 for unlimited, 0 to stop on first failure)
        clean: Whether to clean the manifest by removing missing entries

    Returns:
        0 for success, TorrentError for failures
    """
    try:
        # Check if parent directory exists
        if not os.path.exists(parent_dir):
            return TorrentError(
                message=f"Parent directory does not exist: {parent_dir}",
                error_code=ErrorCode.DIRECTORY_NOT_FOUND,
            )

        # Check if directory is empty
        subdirs = [
            d
            for d in os.listdir(parent_dir)
            if os.path.isdir(os.path.join(parent_dir, d))
        ]
        if not subdirs:
            return TorrentError(
                message=f"Parent directory is empty: {parent_dir}",
                error_code=ErrorCode.EMPTY_DIRECTORY,
            )

        # Create config if not provided
        if config is None:
            config = TorrentConfig(tracker_url=tracker_url)
        else:
            # Update tracker URL in existing config
            config.tracker_url = tracker_url

        if dry_run:
            handle_dry_run(parent_dir, output_dir, config, is_batch=True, force=force)
            return 0

        # Create output directory if not in dry run mode
        os.makedirs(output_dir, exist_ok=True)

        # Initialize manifest
        manifest = ManifestManager(output_dir)
        # Check for missing torrent files
        missing_files = manifest.get_missing_torrents()
        if missing_files:
            if clean:
                click.echo(
                    f"Found {len(missing_files)} missing torrent files. Cleaning manifest..."
                )
                manifest.clean_manifest()
                click.echo("Manifest cleaned. Proceeding with processing...")
            else:
                return TorrentError(
                    message=f"Found {len(missing_files)} missing torrent files. Use --clean to remove invalid entries.",
                    error_code=ErrorCode.MISSING_TORRENT_FILES,
                )

        failures = 0
        processed = 0
        empty_files = 0
        last_error: Optional[TorrentError] = None
        error_codes = set()  # Track unique error codes

        for subdir in sorted(subdirs):
            dir_path = os.path.join(parent_dir, subdir)
            output_path = os.path.join(output_dir, f"{subdir}.torrent")

            try:
                # Skip if already processed and not forcing update
                if manifest.is_directory_processed(dir_path) and not force:
                    click.echo(f"Skipping {subdir} (already processed)")
                    continue

                # Check if directory is empty before attempting to create torrent
                if is_directory_empty(dir_path):
                    failures += 1
                    error = TorrentError(
                        message=f"Directory is empty: {subdir}",
                        error_code=ErrorCode.EMPTY_DIRECTORY,
                    )
                    last_error = error
                    error_codes.add(error.error_code)
                    click.echo(f"Error: {error.message}", err=True)
                    if max_failures >= 0 and failures >= max_failures:
                        return TorrentError(
                            message=f"Maximum failures reached ({failures})",
                            error_code=ErrorCode.MAX_FAILURES_EXCEEDED,
                        )
                    continue

                # Check for existing output file
                if os.path.exists(output_path) and not force:
                    failures += 1
                    error = TorrentError(
                        message=f"Output file already exists: {output_path}. Use --force to overwrite existing files.",
                        error_code=ErrorCode.FILE_EXISTS,
                    )
                    last_error = error
                    error_codes.add(error.error_code)
                    click.echo(f"Error: {error.message}", err=True)
                    if max_failures >= 0 and failures >= max_failures:
                        return TorrentError(
                            message=f"Maximum failures reached ({failures})",
                            error_code=ErrorCode.MAX_FAILURES_EXCEEDED,
                        )
                    continue
                elif os.path.exists(output_path) and force:
                    # Delete existing output file if it exists
                    if os.path.exists(output_path):
                        os.remove(output_path)

                torrent_creator = TorrentCreator(config)

                try:
                    torrent_path = torrent_creator.create(dir_path, output_path)
                    manifest.add_entry(dir_path, torrent_path, force=force)
                    processed += 1
                    click.echo(f"Created torrent for {subdir}")
                except NoDataError as e:
                    empty_files += 1
                    failures += 1
                    error = TorrentError(
                        message=str(e),
                        error_code=ErrorCode.EMPTY_DIRECTORY,
                    )
                    last_error = error
                    error_codes.add(error.error_code)
                    if max_failures >= 0 and failures >= max_failures:
                        return TorrentError(
                            message=f"Maximum failures reached ({failures})",
                            error_code=ErrorCode.MAX_FAILURES_EXCEEDED,
                        )
                    click.echo(f"Error: {error.message}", err=True)
                    continue
                except Exception as e:
                    if isinstance(e, TorrentError):
                        return e
                    return TorrentError(
                        message=str(e),
                        error_code=ErrorCode.TORRENT_CREATION_ERROR,
                        details={"error": str(e)},
                    )

            except Exception as e:
                failures += 1
                click.echo(f"Error processing {subdir}: {e}", err=True)
                if max_failures >= 0 and failures >= max_failures:
                    return TorrentError(
                        message=f"Maximum failures reached ({failures})",
                        error_code=ErrorCode.MAX_FAILURES_EXCEEDED,
                    )

        # Print summary
        click.echo("\nProcessing complete:")
        click.echo(f"✓ Processed: {processed}")
        if empty_files > 0:
            click.echo(f"⚠ Empty files/directories: {empty_files}")
        if failures > 0:
            click.echo(f"❌ Failed: {failures}")
            # If only one directory was attempted and it failed, return its specific error
            if len(subdirs) == 1:
                return last_error or TorrentError(
                    message="Failed to process directory",
                    error_code=ErrorCode.BATCH_PROCESSING_ERROR,
                    details={"directory": str(subdirs[0])},
                )
            # Otherwise return BATCH_PROCESSING_ERROR
            return TorrentError(
                message=f"Failed to process {failures} directories",
                error_code=ErrorCode.BATCH_PROCESSING_ERROR,
                details={"failures": failures},
            )
        return 0

    except Exception as e:
        if isinstance(e, TorrentError):
            return e
        return TorrentError(
            message=str(e),
            error_code=ErrorCode.ERROR,
        )
