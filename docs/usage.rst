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
----------------------

Creating a Single Torrent
~~~~~~~~~~~~~~~~~~~~~~~~

TorrentDirectories provides a command-line interface for common operations.

.. code-block:: bash

    # Create a torrent from a single file
    torrentdirectories file --input path/to/file --output file.torrent --tracker http://example.com/announce

    # Create a torrent from a directory
    torrentdirectories file --input path/to/directory --output /output/directory --tracker http://example.com/announce

    # Create a private torrent
    torrentdirectories file --input path/to/file --output file.torrent --tracker http://example.com/announce --private

Batch Processing
~~~~~~~~~~~~~~~

You can process multiple directories at once:

.. code-block:: bash

    torrentdirectories batch --input path/to/content_dir --output path/to/output_dir --tracker http://example.com/announce


Configuration Options
---------------------

The `TorrentConfig` class provides several options for customizing torrent creation:

.. code-block:: python

    config = TorrentConfig(
        tracker_url="http://example.com/announce",
        private=True,  # Make the torrent private
        comment="My torrent",  # Add a comment
        source="MySource",  # Add a source tag
    )
