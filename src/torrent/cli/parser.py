"""
Command-line argument parsing for TorrentDirectories.
"""

from __future__ import annotations

import argparse
from typing import Dict, Any, Optional

from ..utils.config import TorrentConfig
from .config import parse_size


def create_torrent_config(args: argparse.Namespace) -> Optional[TorrentConfig]:
    """Create torrent configuration from command line arguments."""
    target_pieces = None
    if args.target_pieces:
        try:
            min_pieces, max_pieces = map(int, args.target_pieces.split("-"))
            target_pieces = (min_pieces, max_pieces)
        except ValueError:
            raise ValueError("Target pieces must be in format 'min-max' (e.g. 1000-2000)")

    return TorrentConfig(
        min_piece_size=parse_size(args.min_piece_size) if args.min_piece_size else None,
        max_piece_size=parse_size(args.max_piece_size) if args.max_piece_size else None,
        target_pieces_min=target_pieces[0] if target_pieces else 1000,
        target_pieces_max=target_pieces[1] if target_pieces else 2000,
        skip_hidden=not args.include_hidden,
        skip_system_files=not args.include_system,
    )

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    from torrent import __version__

    parser = argparse.ArgumentParser(
        description="Create torrent files from directories with optimal settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create a torrent for a single file or directory:
    %(prog)s file path/to/content http://tracker.example.com:6969/announce

  Process all subdirectories in a parent directory:
    %(prog)s batch path/to/parent http://tracker.example.com:6969/announce

  Show more detailed output:
    %(prog)s -v batch path/to/parent http://tracker.example.com:6969/announce

  Use custom piece size bounds:
    %(prog)s file --min-piece-size 256K --max-piece-size 32M path/to/content tracker-url
""",
    )

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

    # Global torrent configuration
    torrent_group = parser.add_argument_group("Torrent Creation Options")
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
        "--target-pieces", help="Target piece count range (e.g. 1000-2000)"
    )
    torrent_group.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories",
    )
    torrent_group.add_argument(
        "--include-system", action="store_true", help="Include system files"
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Command to execute"
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

    # Client command
    client_parser = subparsers.add_parser("client", help="Run the torrent client")
    client_parser.add_argument("torrent_dir", help="Directory containing torrent files")
    client_parser.add_argument(
        "--data-dir", help="Directory containing data files (defaults to torrent_dir)"
    )
    client_parser.add_argument(
        "--port", type=int, default=6881, help="Port to listen on"
    )
    client_parser.add_argument(
        "--max-upload-rate",
        type=int,
        default=0,
        help="Maximum upload rate in bytes/s (0 for unlimited)",
    )
    client_parser.add_argument(
        "--max-download-rate",
        type=int,
        default=0,
        help="Maximum download rate in bytes/s (0 for unlimited)",
    )
    client_parser.add_argument(
        "--max-connections",
        type=int,
        default=200,
        help="Maximum number of peer connections",
    )
    client_parser.add_argument(
        "--check-interval",
        type=int,
        default=60,
        help="Interval in seconds to check for new torrents",
    )
    client_parser.add_argument(
        "--auto-restart",
        action="store_true",
        help="Automatically restart the batch process",
    )

    # Batch-specific options
    batch_group = client_parser.add_argument_group("Batch Process Options")
    batch_group.add_argument(
        "--batch-check-interval",
        type=int,
        default=300,
        help="Interval in seconds to check for new directories to process",
    )
    batch_group.add_argument(
        "--batch-max-failures",
        type=int,
        default=0,
        help="Maximum number of failures before stopping the batch process",
    )
    batch_group.add_argument(
        "--batch-clean",
        action="store_true",
        default=True,
        help="Clean the manifest on each batch run",
    )
    batch_group.add_argument(
        "--batch-force",
        action="store_true",
        default=True,
        help="Force recreation of torrents on each batch run",
    )
    batch_group.add_argument(
        "--batch-dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    # Web interface options
    web_group = client_parser.add_argument_group("Web Interface Options")
    web_group.add_argument(
        "--web",
        action="store_true",
        help="Enable the web interface",
    )
    web_group.add_argument(
        "--web-port",
        type=int,
        default=5000,
        help="Port to listen on for the web interface",
    )

    return parser
