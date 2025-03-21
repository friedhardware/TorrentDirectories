"""
Click-based command-line interface for TorrentDirectories.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
from types import FrameType
from typing import List, Optional, cast

import click
from click import Context

from ..error_handling import convert_to_click_error
from ..exceptions import ErrorCode, NoDataError, TorrentError
from ..torrent_creator import TorrentConfig
from ..utils.cli_utils import parse_size
from ..utils.logging_utils import setup_logging
from ..version import __version__
from .commands import handle_dry_run, process_batch, process_single

logger = logging.getLogger(__name__)

# Global flag to track interrupt state
interrupted = False


def signal_handler(signum: int, frame: Optional[FrameType]) -> None:
    """Handle interrupt signal (Ctrl+C)."""
    global interrupted
    if interrupted:  # Second interrupt, exit immediately
        logger.warning("Forced exit due to second interrupt")
        sys.exit(ErrorCode.INTERRUPTED.value)
    interrupted = True
    logger.info("Interrupt received, cleaning up...")
    click.echo("\nInterrupt received. Cleaning up... Press Ctrl+C again to force quit.")


def create_torrent_config(
    ctx: Context,
    min_piece_size: Optional[str],
    max_piece_size: Optional[str],
    include_system: bool,
    public: bool,
    tracker_url: str = "",
) -> TorrentConfig:
    """Create a TorrentConfig from command line arguments."""
    try:
        min_size = parse_size(min_piece_size) if min_piece_size else None
        max_size = parse_size(max_piece_size) if max_piece_size else None
    except ValueError as e:
        raise click.BadParameter(
            f"Invalid piece size format. Use format like '16K', '1M', '32M'. Error: {str(e)}"
        )

    # Validate piece sizes
    if min_size and max_size and min_size > max_size:
        raise click.BadParameter(
            f"Minimum piece size ({min_size // 1024} KiB) cannot be greater than "
            f"maximum piece size ({max_size // 1024} KiB)"
        )

    # Validate tracker URL
    if not tracker_url.startswith(("http://", "https://", "udp://")):
        raise click.BadParameter(
            f"Invalid tracker URL: {tracker_url}. Must start with http://, https://, or udp://"
        )

    return TorrentConfig(
        tracker_url=tracker_url,
        min_piece_size=min_size or 256 * 1024,  # Default to 256K if None
        max_piece_size=max_size or 16 * 1024 * 1024,  # Default to 16M if None
        skip_hidden=True,
        skip_system_files=not include_system,
        private=not public,
    )


@click.group()
@click.version_option(version=__version__)
@click.option("-v", "--verbose", count=True, help="Increase verbosity")
@click.option("--log-file", type=str, help="Log file path")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.option("--force", is_flag=True, help="Overwrite existing torrent files")
@click.pass_context
def cli(
    ctx: Context, verbose: int, log_file: Optional[str], dry_run: bool, force: bool
) -> None:
    """Create torrent files from directories with optimal settings."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    ctx.ensure_object(dict)
    ctx.obj["dry_run"] = dry_run
    ctx.obj["force"] = force
    ctx.obj["interrupted"] = False  # Add interrupted flag to context
    setup_logging(verbose > 0, log_file)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.argument("tracker", type=str)
@click.option(
    "-o", "--output", type=click.Path(), help="Custom output path for the torrent file"
)
@click.option(
    "--min-piece-size",
    type=str,
    default="256K",
    help="Minimum piece size (e.g. 16K, 1M)",
)
@click.option(
    "--max-piece-size",
    type=str,
    default="16M",
    help="Maximum piece size (e.g. 16M, 64M)",
)
@click.option("--include-system", is_flag=True, help="Include system files")
@click.option("--private/--public", default=True, help="Create private/public torrent")
@click.option("--source", type=str, help="Source string for the torrent")
@click.option("--comment", type=str, help="Comment string for the torrent")
@click.pass_context
def file(
    ctx: Context,
    path: str,
    tracker: str,
    output: Optional[str],
    min_piece_size: str,
    max_piece_size: str,
    include_system: bool,
    private: bool,
    source: Optional[str],
    comment: Optional[str],
) -> None:
    """Create a torrent from a single file or directory."""
    try:
        config = create_torrent_config(
            ctx,
            min_piece_size,
            max_piece_size,
            include_system,
            not private,
            tracker_url=tracker,
        )
        config.source = source
        config.comment = comment

        if ctx.obj["dry_run"]:
            handle_dry_run(path, output, config)
            return  # Let Click handle the exit

        result = process_single(
            path=path,
            tracker_url=tracker,
            output=output,
            config=config,
            dry_run=ctx.obj["dry_run"],
            force=ctx.obj["force"],
        )

        if isinstance(result, TorrentError):
            raise convert_to_click_error(result)
        elif result != 0:
            raise click.ClickException("Failed to create torrent")

    except click.ClickException:
        raise
    except NoDataError as e:
        # Handle NoDataError specifically to preserve its error code
        raise convert_to_click_error(e)
    except Exception as e:
        if isinstance(e, TorrentError):
            raise convert_to_click_error(e)
        raise click.ClickException(f"Unexpected error: {e}")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.argument("tracker")
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="torrents/",
    help="Output directory for torrent files",
)
@click.option(
    "--clean", is_flag=True, help="Clean the manifest by removing missing entries"
)
@click.option(
    "--max-failures",
    type=int,
    default=-1,
    help="Maximum allowed failures before stopping (-1 for unlimited, 0 to stop on first failure)",
)
@click.option(
    "--min-piece-size",
    type=str,
    default="256K",
    help="Minimum piece size (e.g. 16K, 1M)",
)
@click.option(
    "--max-piece-size",
    type=str,
    default="16M",
    help="Maximum piece size (e.g. 16M, 64M)",
)
@click.option("--include-system", is_flag=True, help="Include system files")
@click.option("--private/--public", default=True, help="Create private/public torrent")
@click.option("--source", type=str, help="Source string for the torrent")
@click.option("--comment", type=str, help="Comment string for the torrent")
@click.pass_context
def batch(
    ctx: Context,
    directory: str,
    tracker: str,
    output: str,
    clean: bool,
    max_failures: int,
    min_piece_size: str,
    max_piece_size: str,
    include_system: bool,
    private: bool,
    source: Optional[str],
    comment: Optional[str],
) -> None:
    """Process all subdirectories in a parent directory."""
    try:
        config = create_torrent_config(
            ctx,
            min_piece_size,
            max_piece_size,
            include_system,
            not private,
            tracker_url=tracker,
        )
        config.source = source
        config.comment = comment

        # Check if output directory is inside parent directory
        abs_parent = os.path.abspath(directory)
        abs_output = os.path.abspath(output)
        if abs_output.startswith(abs_parent + os.sep):
            click.echo(
                click.style("Warning: ", fg="yellow", bold=True)
                + "Output directory is inside the input directory. This means the output directory will be processed as part of the batch operation."
            )

        if ctx.obj["dry_run"]:
            try:
                handle_dry_run(directory, output, config, is_batch=True)
                return  # Let Click handle the exit
            except TorrentError as e:
                raise convert_to_click_error(e)

        result = process_batch(
            parent_dir=directory,
            tracker_url=tracker,
            config=config,
            output_dir=output,
            dry_run=ctx.obj["dry_run"],
            clean=clean,
            force=ctx.obj["force"],
            max_failures=max_failures,
        )

        if isinstance(result, TorrentError):
            raise convert_to_click_error(result)
        elif result != 0:
            raise click.ClickException("Failed to process directories")

    except click.ClickException:
        raise  # Let Click handle the error display
    except Exception as e:
        if isinstance(e, TorrentError):
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(e.error_code.value)
        logger.exception("Unexpected error")
        click.echo(f"Error: Unexpected error: {e}", err=True)
        sys.exit(ErrorCode.ERROR.value)


def main(args: Optional[List[str]] = None) -> int:
    """Run the CLI application.

    Args:
        args: Optional list of command line arguments.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    try:
        result = cli.main(args=args, standalone_mode=False)
        if result is None:
            return 0
        if isinstance(result, bool):
            return 0 if result else 1
        if isinstance(result, int):
            return cast(int, result)
        if isinstance(result, str):
            try:
                return int(result)
            except (TypeError, ValueError):
                return 1
        # If we get here, result is of an unexpected type
        return 1
    except click.exceptions.Abort:  # Handle Ctrl+C
        logger.info("Operation cancelled by user")
        # Check if we were interrupted by signal handler
        if interrupted:
            return ErrorCode.INTERRUPTED.value
        return 1
    except Exception as e:
        if isinstance(e, SystemExit):
            return cast(int, e.code)
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
