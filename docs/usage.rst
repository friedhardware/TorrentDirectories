Usage
=====

Basic Usage
----------

To create a torrent file from a single file or directory:

.. code-block:: python

    from torrent.torrent_creator import TorrentCreator
    from torrent.utils.config import TorrentConfig

    # Create a configuration with a tracker URL
    config = TorrentConfig(
        tracker_url="http://example.com/announce",
        private=True,  # Optional: make the torrent private (default)
        skip_system_files=True,  # Optional: skip system files (default)
        min_piece_size=256 * 1024,  # Optional: minimum piece size in bytes
        max_piece_size=16 * 1024 * 1024,  # Optional: maximum piece size in bytes
        target_pieces_min=1000,  # Optional: target minimum number of pieces
        target_pieces_max=2000,  # Optional: target maximum number of pieces
    )

    # Initialize the torrent creator
    creator = TorrentCreator(config)

    # Create a torrent file
    creator.create(
        input_path="path/to/content",
        output_path="output.torrent"
    )

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

Common Options
~~~~~~~~~~~~~

General Options (before command):
    * ``--verbose`` or ``-v``: Show detailed progress
    * ``--dry-run``: Preview changes without making them
    * ``--log-file FILE``: Write logs to file

Torrent Options:
    * ``--private | --public``: Set torrent privacy (mutually exclusive, private by default)
    * ``--min-piece-size SIZE``: Minimum piece size (e.g., 16K, 1M)
    * ``--max-piece-size SIZE``: Maximum piece size (e.g., 16M, 64M)
    * ``--include-system``: Include system files
    * ``--force``: Overwrite existing torrents
    * ``-o/--output OUTPUT``: Output path for the torrent(s)

Batch-specific Options:
    * ``--clean``: Clean the manifest by removing missing entries
    * ``--max-failures N``: Maximum failures before stopping (0 for unlimited)

Note: General options must come before the command (file/batch), while torrent-specific options come after.
