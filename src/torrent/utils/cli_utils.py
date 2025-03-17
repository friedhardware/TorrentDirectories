"""
Utility functions for the CLI package.
"""

from __future__ import annotations


def parse_size(size_str: str) -> int:
    """Parse a human-readable size string into bytes.

    Args:
        size_str: Size string (e.g. '1K', '2M', '3G')

    Returns:
        Size in bytes

    Raises:
        ValueError: If size string is invalid
    """
    # Remove any whitespace
    size_str = size_str.strip().upper()

    # Handle empty string
    if not size_str:
        raise ValueError("Size string cannot be empty")

    # Get the unit and number
    unit = size_str[-1]
    try:
        number = float(size_str[:-1])
    except ValueError:
        raise ValueError(f"Invalid size string: {size_str}")

    # Convert to bytes
    if unit == "K":
        size = int(number * 1024)
    elif unit == "M":
        size = int(number * 1024 * 1024)
    elif unit == "G":
        size = int(number * 1024 * 1024 * 1024)
    else:
        raise ValueError(f"Invalid unit: {unit}. Must be K, M, or G")

    return size
