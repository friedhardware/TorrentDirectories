Quick Start Guide
===============

This guide will help you get started with TorrentDirectories quickly. You'll learn how to:

1. Install the tool
2. Create your first torrent
3. Process multiple directories
4. Handle common scenarios

Installation
-----------

Install from source:

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/friedhardware/TorrentDirectories.git
    cd TorrentDirectories

    # Create and activate virtual environment
    python3 -m venv venv
    source venv/bin/activate  # On Unix/macOS
    # Or on Windows: venv\Scripts\activate

    # Install in development mode
    pip install -e .

First Torrent: Single File/Directory
-----------------------------------

Create a torrent from a single file or directory:

.. code-block:: bash

    # Basic usage - create private torrent
    torrent-directories file path/to/content http://tracker.example.com/announce

    # The torrent will be saved as path/to/content.torrent in the current directory

You'll see output confirming successful creation:

.. code-block:: bash

    Torrent created successfully: path/to/content.torrent

Customizing Your Torrent
-----------------------

Add metadata and customize settings:

.. code-block:: bash

    torrent-directories file path/to/content http://tracker.example.com/announce \
        --comment "My awesome release" \
        --source "MyGroup" \
        --min-piece-size 512K \
        -o my_custom_name.torrent

Batch Processing Multiple Directories
-----------------------------------

Process all subdirectories in a parent directory:

.. code-block:: bash

    # Create a directory for output
    mkdir -p torrents

    # Process all subdirectories
    torrent-directories batch ./media_collection http://tracker.example.com/announce \
        -o ./torrents

This will:
1. Create a torrent for each subdirectory in `media_collection`
2. Save them to the `torrents` directory
3. Create a manifest file to track processed directories

You'll see output like:

.. code-block:: bash

    Created torrent for movie1
    Created torrent for movie2
    Created torrent for movie3

    Processed 3 new directories

Real-World Examples
-----------------

Example 1: Processing a TV Series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's say you have a directory structure like:

.. code-block:: text

    /media/TV/
    ├── Show1/
    │   ├── Season 1/
    │   └── Season 2/
    ├── Show2/
    │   └── Season 1/
    └── Show3/
        ├── Season 1/
        └── Season 2/

To create a torrent for each show:

.. code-block:: bash

    torrent-directories batch /media/TV http://tracker.example.com/announce \
        -o /media/torrents \
        --comment "TV Collection" \
        --private

Example 2: Updating a Music Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you've added new albums to your collection:

.. code-block:: bash

    # Process only new albums (already processed ones are skipped)
    torrent-directories batch /media/Music http://tracker.example.com/announce \
        -o /media/torrents \
        --skip-empty-files

Example 3: Creating a Torrent for a Large Movie
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For larger files, you might want to adjust the piece size:

.. code-block:: bash

    torrent-directories file /media/Movies/BigMovie.mkv \
        http://tracker.example.com/announce \
        -o "Big Movie.torrent" \
        --min-piece-size 1M \
        --max-piece-size 16M \
        --comment "4K HDR Movie" \
        --source "MyGroup"

Common Issues and Solutions
-------------------------

1. Empty files in your directory:

.. code-block:: bash

    # Skip empty files instead of failing
    torrent-directories file path/to/content http://tracker.example.com/announce \
        --skip-empty-files

2. Need to overwrite existing torrents:

.. code-block:: bash

    # Use the force option
    torrent-directories file path/to/content http://tracker.example.com/announce \
        --force -o existing.torrent

3. Missing torrent files in batch mode:

.. code-block:: bash

    # Clean the manifest and recreate missing torrents
    torrent-directories batch path/to/parent http://tracker.example.com/announce \
        --clean

4. Seeing what would happen before making changes:

.. code-block:: bash

    # Use dry run mode
    torrent-directories --dry-run batch path/to/parent http://tracker.example.com/announce

Next Steps
---------

- Read the :doc:`usage` guide for more detailed options
- Check the :doc:`api/index` for Python API documentation
- See :doc:`contributing` to help improve the project

For more detailed information on any command, use the ``--help`` option:

.. code-block:: bash

    torrent-directories --help
    torrent-directories file --help
    torrent-directories batch --help
