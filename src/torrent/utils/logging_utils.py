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

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        root_logger.addHandler(file_handler)


def log_progress(message: str, success: bool = True) -> None:
    """
    Display a progress message with a checkmark or cross.

    Args:
        message: Message to display
        success: Whether the operation was successful
    """
    status = "✓" if success else "✗"
    click.echo(f"  {message}: {status}")


def log_batch_progress(subdir: str, torrent_path: Optional[str] = None) -> None:
    """
    Display a batch processing progress message.

    Args:
        subdir: Name of the subdirectory being processed
        torrent_path: Optional path to the created torrent file
    """
    if torrent_path:
        click.echo(f"  {subdir}: Created {torrent_path}")
    else:
        click.echo(f"  {subdir}: Already processed")
