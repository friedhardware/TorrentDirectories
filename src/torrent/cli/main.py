"""
Main entry point for the command-line interface.
"""

from __future__ import annotations

import logging
import sys
from argparse import Namespace
from typing import List, Optional

from .commands import process_batch, process_single
from .config import create_torrent_config
from .parser import create_parser

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


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the command-line interface.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    parsed_args: Namespace = parser.parse_args(args)

    try:
        # Setup logging first
        setup_logging(parsed_args.verbose, parsed_args.log_file)

        # Create torrent configuration from arguments
        config = create_torrent_config(parsed_args)

        if parsed_args.command == "file":
            return process_single(
                parsed_args.path,
                parsed_args.tracker,
                parsed_args.output,
                config=config,
                dry_run=parsed_args.dry_run,
                force=parsed_args.force,
            )
        elif parsed_args.command == "batch":
            return process_batch(
                parsed_args.directory,
                parsed_args.tracker,
                clean=parsed_args.clean,
                config=config,
                output_dir=parsed_args.output,
                dry_run=parsed_args.dry_run,
                force=parsed_args.force,
                max_failures=parsed_args.max_failures,
            )
        else:
            parser.print_help()
            return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if parsed_args.verbose:
            logger.exception("Detailed error information:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
