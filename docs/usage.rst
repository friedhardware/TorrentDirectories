Usage Guide
===========

This guide covers the main features and usage patterns of TorrentDirectories.

Basic Usage
----------

Creating a Single Torrent
~~~~~~~~~~~~~~~~~~~~~~~~

To create a torrent from a single file or directory::

    torrent-directories file <path> <tracker_url> [options]

Example::

    # Create a private torrent (default)
    torrent-directories file path/to/content http://tracker.example.com/announce

    # Specify output location
    torrent-directories file path/to/content http://tracker.example.com/announce -o output.torrent

    # Create a public torrent with metadata
    torrent-directories file path/to/content http://tracker.example.com/announce \
        --public \
        --source "My Release Group" \
        --comment "Great content!"

Batch Processing
~~~~~~~~~~~~~~~

Process multiple directories at once::

    torrent-directories batch <parent_directory> <tracker_url> [options]

Example::

    # Process all subdirectories
    torrent-directories batch path/to/parent http://tracker.example.com/announce

    # Specify output directory and clean manifest
    torrent-directories batch path/to/parent http://tracker.example.com/announce \
        -o path/to/torrents \
        --clean

    # Process with custom settings and force rebuild
    torrent-directories batch path/to/parent http://tracker.example.com/announce \
        --min-piece-size 1M \
        --max-piece-size 32M \
        --force

Common Options
-------------

Global Options
~~~~~~~~~~~~~

These options can be used with any command:

- ``--version``: Show version information
- ``--verbose`` or ``-v``: Show detailed progress
- ``--dry-run``: Preview changes without making them
- ``--log-file FILE``: Write logs to file
- ``--force``: Overwrite existing torrent files

Torrent Options
~~~~~~~~~~~~~~

These options control torrent creation:

- ``--private | --public``: Set torrent privacy (default: private)
- ``--min-piece-size SIZE``: Minimum piece size (e.g., 16K, 1M, default: 256K)
- ``--max-piece-size SIZE``: Maximum piece size (e.g., 16M, 64M, default: 16M)
- ``--include-system``: Include system files (default: False)
- ``--source TEXT``: Add a source string to the torrent metadata
- ``--comment TEXT``: Add a comment to the torrent metadata
- ``-o/--output OUTPUT``: Output path for the torrent(s)

Batch-specific Options
~~~~~~~~~~~~~~~~~~~~

Additional options for batch processing:

- ``--clean``: Clean the manifest by removing missing entries
- ``--max-failures N``: Maximum failures before stopping (0 for unlimited)

Error Handling
-------------

The tool provides detailed error messages and appropriate exit codes:

File Existence
~~~~~~~~~~~~~

- Checks for existing files before creation
- Provides clear messages about using ``--force`` to overwrite
- Creates backups when overwriting with ``--force``

Progress Reporting
~~~~~~~~~~~~~~~~

- Shows real-time progress in verbose mode
- Reports file counts and sizes
- Displays percentage completion for large operations


Maximum Failures
~~~~~~~~~~~~~~

- In batch mode, use ``--max-failures N`` to control error tolerance
- 0 means continue regardless of failures
- Reports failed items in summary

Manifest System
-------------

The manifest system tracks processed directories in batch mode:

Structure
~~~~~~~~

The manifest is stored as a CSV file with the following format::

    "directory_path","torrent_file","processed_at"
    "/path/to/movie1","movie1.torrent","2024-03-15T14:30:00"
    "/path/to/movie2","movie2.torrent","2024-03-15T14:31:00"

Features
~~~~~~~~

- Automatic skipping of already processed directories
- Manifest cleaning with ``--clean`` option
- Automatic backup before cleaning
- Thread-safe operations for concurrent access
- Caching system for improved performance

Cache System
~~~~~~~~~~~

The manifest cache system provides:

- Efficient lookup of processed directories
- Automatic cache invalidation on changes
- Size-limited caching to control memory usage
- Thread-safe cache operations

Advanced Usage
-------------

Dry Run Mode
~~~~~~~~~~~

Use ``--dry-run`` to preview changes::

    torrent-directories --dry-run batch ./movies http://tracker.example.com/announce

This shows:

- Files that would be processed
- Output locations
- Total size and file counts
- Configuration that would be used

Logging
~~~~~~~

Control logging output:

- Use ``-v`` for detailed progress
- Use ``--log-file`` to save logs
- Logs include timestamps and operation details
- Unicode support for international file names

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~

The tool automatically optimizes:

- Piece sizes based on content
- Cache usage for batch operations
- File system operations
- Progress reporting frequency

Security Features
~~~~~~~~~~~~~~~

Built-in security measures:

- File locking for concurrent access
- Backup creation before modifications
- Permission checking
- Safe handling of special files
