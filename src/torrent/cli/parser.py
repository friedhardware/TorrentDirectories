"""
Command-line argument parsing for TorrentDirectories.
"""

from __future__ import annotations

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    from torrent import __version__

    parser = argparse.ArgumentParser(
        description="Create torrent files from directories with optimal settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create a private torrent (default):
    %(prog)s file path/to/content http://tracker.example.com/announce --private

  Create a public torrent:
    %(prog)s file path/to/content http://tracker.example.com/announce --public

  Process all subdirectories with verbose output:
    %(prog)s -v batch path/to/parent http://tracker.example.com/announce

  Create torrent with custom piece size:
    %(prog)s file path/to/content tracker-url --min-piece-size 256K --max-piece-size 32M
""",
    )

    # General options (before command)
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed progress information",
    )
    parser.add_argument("--log-file", help="Write logs to specified file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Command to execute"
    )

    # Common torrent options for both commands
    def add_torrent_options(cmd_parser: argparse.ArgumentParser) -> None:
        """Add common torrent creation options to a subcommand parser."""
        torrent_group = cmd_parser.add_argument_group("Torrent Creation Options")
        torrent_group.add_argument(
            "--min-piece-size",
            type=str,
            help="Minimum piece size (e.g. 16K, 1M). Default: 256K. Must be at least 16K.",
            default="256K",
        )
        torrent_group.add_argument(
            "--max-piece-size",
            type=str,
            help="Maximum piece size (e.g. 16M, 64M). Default: 16M. Cannot exceed 64M.",
            default="16M",
        )
        torrent_group.add_argument(
            "--target-pieces",
            help="Target piece count range (e.g. 1000-2000)",
        )
        torrent_group.add_argument(
            "--include-system",
            action="store_true",
            help="Include system files",
        )
        
        # Create mutually exclusive group for private/public flags
        visibility_group = torrent_group.add_mutually_exclusive_group()
        visibility_group.add_argument(
            "--private",
            action="store_true",
            help="Create private torrents (default)",
        )
        visibility_group.add_argument(
            "--public",
            action="store_true",
            help="Create public torrents",
        )

    # Single file/directory command
    file_parser = subparsers.add_parser(
        "file", help="Create a torrent from a single file or directory"
    )
    file_parser.add_argument("path", help="Path to the file or directory")
    file_parser.add_argument("tracker", help="Tracker URL")
    file_parser.add_argument(
        "-o", "--output", help="Custom output path for the torrent file"
    )
    file_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing torrent file"
    )
    add_torrent_options(file_parser)

    # Batch processing command
    batch_parser = subparsers.add_parser(
        "batch", help="Process all subdirectories in a parent directory"
    )
    batch_parser.add_argument("directory", help="Parent directory to process")
    batch_parser.add_argument("tracker", help="Tracker URL")
    batch_parser.add_argument(
        "-o", "--output", help="Output directory for torrent files and manifest"
    )
    batch_parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean the manifest by removing missing entries",
    )
    batch_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing torrent files"
    )
    batch_parser.add_argument(
        "--max-failures",
        type=int,
        default=0,
        help="Maximum allowed failures before stopping (0 for unlimited)",
    )
    add_torrent_options(batch_parser)

    return parser
