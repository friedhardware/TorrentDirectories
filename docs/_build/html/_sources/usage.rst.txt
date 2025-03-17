Usage Guide
===========

This guide will walk you through the main features of TorrentDirectories.

Basic Usage
----------

Creating a Simple Torrent
~~~~~~~~~~~~~~~~~~~~~~~~

To create a torrent file from a single file or directory:

.. code-block:: python

    from torrent.torrent_creator import TorrentCreator
    from torrent.utils.config import TorrentConfig

    # Create a configuration with a tracker URL
    config = TorrentConfig(
        tracker_url="http://example.com/announce",
        private=True  # Optional: make the torrent private
    )

    # Initialize the torrent creator
    creator = TorrentCreator(config)

    # Create a torrent file
    creator.create(
        input_path="path/to/content",
        output_path="output.torrent"
    )

Command Line Interface
--------------------

TorrentDirectories provides a command-line interface for common operations.

Creating a Torrent
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Create a torrent from a single file
    torrentdirectories create --input path/to/file --output file.torrent --tracker http://example.com/announce

    # Create a torrent from a directory
    torrentdirectories create --input path/to/directory --output directory.torrent --tracker http://example.com/announce

    # Create a private torrent
    torrentdirectories create --input path/to/content --output content.torrent --tracker http://example.com/announce --private

Batch Processing
~~~~~~~~~~~~~~~

You can process multiple files or directories at once:

.. code-block:: bash

    torrentdirectories batch --input path/to/content_dir --output path/to/output_dir --tracker http://example.com/announce

Advanced Features
----------------

Manifest Management
~~~~~~~~~~~~~~~~~

TorrentDirectories maintains a manifest of created torrents. You can clean the manifest to remove invalid entries:

.. code-block:: python

    from torrent.manifest import ManifestManager

    # Initialize the manifest manager
    manager = ManifestManager()

    # Clean the manifest
    manager.clean_manifest()

Configuration Options
~~~~~~~~~~~~~~~~~~~

The `TorrentConfig` class provides several options for customizing torrent creation:

.. code-block:: python

    config = TorrentConfig(
        tracker_url="http://example.com/announce",
        private=True,  # Make the torrent private
        comment="My torrent",  # Add a comment
        source="MySource",  # Add a source tag
    )

Piece Size Calculation
~~~~~~~~~~~~~~~~~~~~

TorrentDirectories automatically calculates the optimal piece size based on the content size:

- Small files (< 50MB): 16KB pieces
- Medium files (50MB - 1GB): 256KB pieces
- Large files (> 1GB): 1MB pieces

You can see the calculated piece size in the debug logs:

.. code-block:: python

    import logging

    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)

    # Create your torrent as usual
    creator.create("path/to/content", "output.torrent")

Error Handling
-------------

TorrentDirectories provides clear error messages for common issues:

.. code-block:: python

    try:
        creator.create("nonexistent/path", "output.torrent")
    except ValueError as e:
        print(f"Error creating torrent: {e}")

    try:
        creator.create("path/to/content", "invalid/output/path/output.torrent")
    except OSError as e:
        print(f"Error writing torrent file: {e}") 