"""
Click-based command-line interface for TorrentDirectories.
"""

from __future__ import annotations

import logging
from typing import Optional

import click
from click import Context

from ..utils.cli_utils import parse_size
from ..utils.config import TorrentConfig
from ..utils.logging_utils import setup_logging
from ..version import __version__
from .commands import process_batch, process_single
from .exceptions import OutputFileExistsError

logger = logging.getLogger(__name__)


def create_torrent_config(
    ctx: Context,
    min_piece_size: Optional[str],
    max_piece_size: Optional[str],
    include_system: bool,
    public: bool,
    skip_empty_files: bool = False,
    tracker_url: str = "",
) -> TorrentConfig:
    """Create a TorrentConfig from command line arguments."""
    min_size = parse_size(min_piece_size) if min_piece_size else None
    max_size = parse_size(max_piece_size) if max_piece_size else None

    return TorrentConfig(
        tracker_url=tracker_url,
        min_piece_size=min_size or 256 * 1024,  # Default to 256K if None
        max_piece_size=max_size or 16 * 1024 * 1024,  # Default to 16M if None
        skip_hidden=True,
        skip_system_files=not include_system,
        private=not public,
        skip_empty_files=skip_empty_files,
    )


@click.group()
@click.version_option(version=__version__, prog_name="torrent-directories")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed progress information"
)
@click.option("--log-file", type=click.Path(), help="Write logs to specified file")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without making changes"
)
@click.pass_context
def cli(ctx: Context, verbose: bool, log_file: Optional[str], dry_run: bool) -> None:
    """Create torrent files from directories with optimal settings."""
    setup_logging(verbose, log_file)
    ctx.ensure_object(dict)
    ctx.obj["dry_run"] = dry_run


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.argument("tracker")
@click.option(
    "-o", "--output", type=click.Path(), help="Custom output path for the torrent file"
)
@click.option("--force", is_flag=True, help="Overwrite existing torrent file")
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
@click.option("--skip-empty", is_flag=True, help="Skip empty files")
@click.option("--source", type=str, help="Source string for the torrent")
@click.option("--comment", type=str, help="Comment string for the torrent")
@click.pass_context
def file(
    ctx: Context,
    path: str,
    tracker: str,
    output: Optional[str],
    force: bool,
    min_piece_size: str,
    max_piece_size: str,
    include_system: bool,
    private: bool,
    skip_empty: bool,
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
            skip_empty_files=skip_empty,
            tracker_url=tracker,
        )
        config.source = source
        config.comment = comment

        exit_code = process_single(
            path=path,
            tracker_url=tracker,
            output=output,
            config=config,
            dry_run=ctx.obj["dry_run"],
            force=force,
        )
        if exit_code != 0:
            raise click.ClickException("Failed to create torrent")

    except OutputFileExistsError as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(str(e))


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
@click.option("--force", is_flag=True, help="Overwrite existing torrent files")
@click.option(
    "--max-failures",
    type=int,
    default=0,
    help="Maximum allowed failures before stopping",
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
@click.option("--skip-empty", is_flag=True, help="Skip empty files")
@click.option("--source", type=str, help="Source string for the torrent")
@click.option("--comment", type=str, help="Comment string for the torrent")
@click.pass_context
def batch(
    ctx: Context,
    directory: str,
    tracker: str,
    output: str,
    clean: bool,
    force: bool,
    max_failures: int,
    min_piece_size: str,
    max_piece_size: str,
    include_system: bool,
    private: bool,
    skip_empty: bool,
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
            skip_empty_files=skip_empty,
            tracker_url=tracker,
        )
        config.source = source
        config.comment = comment

        exit_code = process_batch(
            directory=directory,
            tracker_url=tracker,
            config=config,
            output_dir=output,
            dry_run=ctx.obj["dry_run"],
            clean=clean,
            force=force,
            max_failures=max_failures,
        )
        if exit_code != 0:
            if not skip_empty:
                raise click.ClickException("Failed to process directories")
            else:
                click.echo("Completed with skipped empty files", err=True)
                ctx.exit(
                    0
                )  # Explicitly exit with success code when skipping empty files

    except Exception as e:
        raise click.ClickException(str(e))


def main() -> int:
    """Main entry point for the command-line interface."""
    try:
        cli()
        return 0
    except click.ClickException as e:
        click.echo(str(e), err=True)
        return 1
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        return 1


if __name__ == "__main__":
    exit(main())
