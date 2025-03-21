"""
Error handling utilities for converting between domain and presentation layer errors.
"""

from __future__ import annotations

import logging
from typing import Any

import click

from .exceptions import ErrorCode, TorrentError

logger = logging.getLogger(__name__)


def convert_to_click_error(error: Exception) -> click.ClickException:
    """Convert a TorrentError to a ClickException with appropriate formatting.

    This function handles the conversion of domain-specific exceptions to Click-formatted
    exceptions that can be properly displayed to users of the CLI. It includes specific
    help text and formatting based on the error type and code.

    Args:
        error: The exception to convert, typically a TorrentError

    Returns:
        A ClickException with formatted error message and appropriate exit code
    """
    logger.debug(
        f"Converting error: {error}, type: {type(error)}, is TorrentError: {isinstance(error, TorrentError)}"
    )
    if isinstance(error, TorrentError):
        # Use the error code value directly from the enum
        exit_code = error.error_code.value
        logger.debug(f"Using error code: {exit_code} from {error.error_code}")

        # Build the error message with code and details
        msg = [
            click.style(f"Error [{error.error_code.name}]", fg="red", bold=True),
            click.style(str(error.message), fg="red"),
        ]

        # Add specific help text based on error code
        help_text = _get_error_help_text(error)
        if help_text:
            msg.append("\n" + click.style("Suggestion:", fg="yellow", bold=True))
            msg.append(click.style(help_text, fg="yellow"))

        # Add details if present
        if hasattr(error, "details") and error.details:
            details_text = _format_error_details(error.details)
            if details_text:
                msg.append("\n" + click.style("Details:", fg="blue", bold=True))
                msg.append(click.style(details_text, fg="blue"))

        # Log additional details for debugging
        if hasattr(error, "details") and error.details:
            logger.debug("Error details: %s", error.details)

        # Create Click exception with the specific error code
        exc = click.ClickException("\n".join(msg))
        exc.exit_code = exit_code
        logger.debug(f"Created ClickException with exit_code: {exc.exit_code}")
        return exc
    else:
        # Handle non-TorrentError exceptions with general error code 1
        logger.debug("Handling non-TorrentError exception")
        exc = click.ClickException(
            click.style("Unexpected error: ", fg="red", bold=True)
            + click.style(str(error), fg="red")
        )
        exc.exit_code = ErrorCode.ERROR.value
        return exc


def _get_error_help_text(error: TorrentError) -> str:
    """Get help text for specific error codes."""
    help_texts = {
        ErrorCode.NO_DATA: "No data found to create torrent from. Directory or file is empty.",
        ErrorCode.EMPTY_DIRECTORY: "Directory must contain at least one non-empty file.",
        ErrorCode.FILE_EXISTS: "Use --force to overwrite existing files.",
        ErrorCode.NO_SUBDIRECTORIES: "Ensure the directory contains at least one subdirectory for batch processing.",
        ErrorCode.MISSING_TORRENT_FILES: "Use --clean to remove missing files from the manifest, or restore the missing files.",
        ErrorCode.MAX_FAILURES_EXCEEDED: "Increase --max-failures or fix the failing items before retrying.",
        ErrorCode.TORRENT_CREATION_ERROR: "Check file permissions and ensure all files are accessible.",
        ErrorCode.INVALID_TRACKER_URL: "Verify the tracker URL format and ensure it's accessible.",
        ErrorCode.FILE_NOT_FOUND: "Verify that the specified file or directory exists.",
    }
    return help_texts.get(error.error_code, "")


def _format_error_details(details: dict[str, Any]) -> str:
    """Format error details into a readable string.

    Args:
        details: Dictionary of error details

    Returns:
        Formatted string of error details
    """
    if not details:
        return ""

    formatted = []
    for key, value in details.items():
        # Format key with proper spacing and capitalization
        formatted_key = key.replace("_", " ").title()

        # Handle different types of values
        if isinstance(value, (list, tuple)):
            formatted_value = "\n  - " + "\n  - ".join(str(v) for v in value)
        elif isinstance(value, dict):
            formatted_value = "\n  " + "\n  ".join(
                f"{k}: {v}" for k, v in value.items()
            )
        else:
            formatted_value = str(value)

        formatted.append(f"{formatted_key}: {formatted_value}")

    return "\n".join(formatted)


def get_error_message(error: TorrentError) -> str:
    """Get a user-friendly error message for a TorrentError."""
    if error.error_code == ErrorCode.FILE_EXISTS:
        return (
            "Output file already exists.\n" "Use --force to overwrite existing files."
        )
    elif error.error_code == ErrorCode.NO_DATA:
        return "No data found to create torrent from.\n" "Directory or file is empty."
    elif error.error_code == ErrorCode.MAX_FAILURES_EXCEEDED:
        return (
            "Maximum failures reached.\n"
            "Use --max-failures 0 to process all directories regardless of failures."
        )
    elif error.error_code == ErrorCode.EMPTY_DIRECTORY:
        return "Directory is empty."
    elif error.error_code == ErrorCode.NO_SUBDIRECTORIES:
        return "No subdirectories found."
    elif error.error_code == ErrorCode.MISSING_TORRENT_FILES:
        return (
            "Found missing torrent files.\n"
            "Use --clean to remove invalid entries from manifest."
        )
    else:
        return str(error)
