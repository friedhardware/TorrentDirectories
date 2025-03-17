"""
Utilities for logging and console output.
"""

import logging
from typing import Optional

import click

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """Configure logging with appropriate level and format."""
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


def log_and_echo(message: str, level: str = "info", echo: bool = True) -> None:
    """
    Log a message and optionally echo it to the console.

    Args:
        message: Message to log and echo
        level: Logging level (debug, info, warning, error)
        echo: Whether to echo the message to console
    """
    log_func = getattr(logger, level.lower())
    log_func(message)

    if echo:
        if level.lower() == "error":
            click.echo(message, err=True)
        else:
            click.echo(message)


def log_progress(message: str, success: bool = True) -> None:
    """
    Log a progress message with a checkmark or cross.

    Args:
        message: Message to log
        success: Whether the operation was successful
    """
    status = "✓" if success else "✗"
    log_and_echo(f"  {message}: {status}")


def log_batch_progress(subdir: str, torrent_path: Optional[str] = None) -> None:
    """
    Log a batch processing progress message.

    Args:
        subdir: Name of the subdirectory being processed
        torrent_path: Optional path to the created torrent file
    """
    if torrent_path:
        log_and_echo(f"  {subdir}: Created {torrent_path}")
    else:
        log_and_echo(f"  {subdir}: Already processed")
