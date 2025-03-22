"""
Utilities for logging and console output.
"""

import logging
from typing import Optional

import click

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool | int = False, log_file: Optional[str] = None) -> None:
    """Configure logging with appropriate level and format.

    Args:
        verbose: If True, enables more detailed logging. The number of -v flags determines the level:
                -v: DEBUG with basic progress
                -vv: DEBUG with detailed progress
                -vvv: DEBUG with extra debug information
        log_file: Optional path to a log file where logs will be written
    """
    root_logger = logging.getLogger()

    # Set log level based on verbosity
    if isinstance(verbose, bool):
        # Backward compatibility for bool verbose
        root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    else:
        # Handle multiple verbosity levels
        if verbose >= 3:
            root_logger.setLevel(logging.DEBUG)
            logging.getLogger("torrent").setLevel(logging.DEBUG)
        elif verbose >= 2:
            root_logger.setLevel(logging.DEBUG)
            logging.getLogger("torrent").setLevel(logging.DEBUG)
        elif verbose >= 1:
            root_logger.setLevel(logging.DEBUG)
            logging.getLogger("torrent").setLevel(logging.DEBUG)
        else:
            root_logger.setLevel(logging.WARNING)
            logging.getLogger("torrent").setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with appropriate formatting
    console_handler = logging.StreamHandler()
    if verbose >= 3:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    elif verbose >= 2:
        formatter = logging.Formatter("%(levelname)s - %(message)s")
    else:
        formatter = logging.Formatter("%(message)s")

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified - always use debug level and detailed format for log files
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always use DEBUG level for file logging
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
