Usage
=====

Basic Usage
----------

To create a torrent file from a single file or directory:

.. code-block:: python

    from torrent.torrent_creator import TorrentCreator
    from torrent.utils.config import TorrentConfig

    # Create configuration
    config = TorrentConfig(
        min_piece_size=256 * 1024,  # 256 KiB minimum piece size
        max_piece_size=16 * 1024 * 1024,  # 16 MiB maximum piece size
        skip_hidden=True,  # Skip hidden files
        skip_system_files=True,  # Skip system files
        private=True,  # Create private torrent
        skip_empty_files=False,  # Don't skip empty files
        tracker_url="http://example.com/announce"  # Tracker URL
    )

    # Create torrent creator
    creator = TorrentCreator(config)

    # Create torrent file
    creator.create("path/to/directory", "output.torrent")

Command Line Interface
----------------------

Creating a Single Torrent
~~~~~~~~~~~~~~~~~~~~~~~~

TorrentDirectories provides a command-line interface for common operations.

.. code-block:: bash

    # Create a private torrent from a single file or directory (default)
    torrent-directories file path/to/content http://tracker.example.com/announce

    # Create a public torrent with custom output location
    torrent-directories file path/to/content http://tracker.example.com/announce --public -o output.torrent

    # Create a torrent with custom piece size settings
    torrent-directories file path/to/content http://tracker.example.com/announce \
        --min-piece-size 1M \
        --max-piece-size 32M \
        --target-pieces 1000-2000

    # Preview changes without creating files (dry run)
    torrent-directories --dry-run file path/to/content http://tracker.example.com/announce

Batch Processing
~~~~~~~~~~~~~~~

You can process multiple directories at once:

.. code-block:: bash

    # Process all subdirectories in a parent directory
    torrent-directories batch path/to/parent http://tracker.example.com/announce

    # Specify output directory for torrent files
    torrent-directories batch path/to/parent http://tracker.example.com/announce -o path/to/torrents

    # Process with custom settings and force rebuild
    torrent-directories batch path/to/parent http://tracker.example.com/announce \
        --min-piece-size 1M \
        --force \
        --include-system

    # Clean manifest and process directories
    torrent-directories batch path/to/parent http://tracker.example.com/announce --clean

Common Options
~~~~~~~~~~~~~

Global Options (before command):
    * ``--version``: Show version information
    * ``--verbose`` or ``-v``: Show detailed progress
    * ``--dry-run``: Preview changes without making them
    * ``--log-file FILE``: Write logs to file

Torrent Options:
    * ``--private | --public``: Set torrent privacy (mutually exclusive, private by default)
    * ``--min-piece-size SIZE``: Minimum piece size (e.g., 16K, 1M)
    * ``--max-piece-size SIZE``: Maximum piece size (e.g., 16M, 64M)
    * ``--target-pieces MIN-MAX``: Target piece count range (e.g., 1000-2000)
    * ``--include-system``: Include system files
    * ``--force``: Overwrite existing torrents
    * ``-o/--output OUTPUT``: Output path for the torrent(s):
        * Single mode: Output file path (default: input name + .torrent)
        * Batch mode: Output directory (default: torrents/)

Batch-specific Options:
    * ``--clean``: Clean the manifest by removing missing entries
    * ``--max-failures N``: Maximum failures before stopping (0 for unlimited)

Manifest System
~~~~~~~~~~~~~

The tool maintains a manifest file to track processed directories in batch mode. This enables:

* Skipping already processed directories
* Resuming interrupted batch operations
* Tracking which directories have been processed

The manifest is stored as a CSV file in the output directory with the following format:

.. code-block:: csv

    directory_path,torrent_file,processed_at
    "/path/to/movie1","movie1.torrent","2024-03-15T14:30:00"

## Piece Size Selection

The piece size is automatically selected based on the following rules:
1. Must be a power of 2 (e.g. 16 KiB, 32 KiB, 64 KiB, etc.)
2. Must be a multiple of 16 KiB
3. Must be between min_piece_size and max_piece_size

The default configuration uses:
- Minimum piece size: 256 KiB
- Maximum piece size: 16 MiB

You can customize these values when creating the config:

.. code-block:: python

    config = TorrentConfig(
        min_piece_size=16 * 1024,  # 16 KiB minimum
        max_piece_size=64 * 1024 * 1024,  # 64 MiB maximum
    )
