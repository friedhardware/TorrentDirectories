"""
Main entry point for the command-line interface.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Optional, Sequence

from ..client.client import run_client
from ..version import __version__
from .commands import process_batch, process_single
from .parser import create_parser, create_torrent_config

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """
    Configure logging with appropriate level and format.

    Args:
        verbose: Whether to show debug level messages
        log_file: Optional path to write logs to
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    format_str = (
        "%(asctime)s - %(levelname)s - %(message)s" if verbose else "%(message)s"
    )
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(format_str))
    root_logger.addHandler(console)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        root_logger.addHandler(file_handler)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main entry point."""
    try:
        parser = create_parser()
        args = parser.parse_args(argv)
        setup_logging(args.verbose, args.log_file)

        if hasattr(args, "version") and args.version:
            print(f"torrent-directories {__version__}")
            return 0

        if args.command == "file":
            return process_single(
                args.path,
                args.tracker,
                args.output,
                config=create_torrent_config(args),
                force=args.force,
            )
        elif args.command == "batch":
            return process_batch(
                args.directory,
                args.tracker,
                clean=args.clean,
                config=create_torrent_config(args),
                output_dir=args.output,
                force=args.force,
                max_failures=args.max_failures,
            )
        elif args.command == "client":
            # Create batch config if auto-restart is enabled
            batch_config = None
            if args.auto_restart:
                batch_config = {
                    "directory": args.torrent_dir,
                    "tracker": args.tracker,
                    "config": create_torrent_config(args),
                    "output_dir": args.torrent_dir,
                    "clean": True,  # Clean manifest on restart
                    "force": True,  # Force recreation of torrents
                }

            return int(
                asyncio.run(
                    run_client(
                        torrent_dir=args.torrent_dir,
                        data_dir=args.data_dir,
                        port=args.port,
                        max_upload_rate=args.max_upload_rate,
                        max_download_rate=args.max_download_rate,
                        max_connections=args.max_connections,
                        check_interval=args.check_interval,
                        auto_restart=args.auto_restart,
                        batch_config=batch_config,
                        web=args.web,
                        web_port=args.web_port,
                    )
                )
            )
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

        return 0
    except Exception as e:
        if args.verbose:
            logger.error(f"Unexpected error: {str(e)}")
            logger.debug("", exc_info=True)
        else:
            logger.error(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
