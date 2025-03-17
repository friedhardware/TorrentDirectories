.. TorrentDirectories documentation master file, created by
   sphinx-quickstart on Sun Mar 16 19:24:41 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TorrentDirectories's documentation!
==============================================

TorrentDirectories is a Python tool for creating torrent files from directories with optimal settings and batch processing capabilities. It provides a simple interface for creating torrent files from both single files and directories, with features like automatic piece size calculation, torrent verification, and batch processing with manifest support.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api/index
   contributing
   changelog

Features
--------

* Create torrents from single files or directories
* Batch process multiple directories with resume support
* Automatic optimal piece size calculation
* Private torrents by default (with public option)
* Detailed logging and progress reporting
* Resume support via manifest system
* Torrent verification after creation
* Cross-platform support (Windows, macOS, Linux)

Requirements
-----------

* Python 3.13 or later
* libtorrent 2.0.0 or later
* click 8.1.3 or later

Installation
------------

You can install TorrentDirectories using pip:

.. code-block:: bash

   pip install torrent-directories

Quick Start
==========

Here's a simple example of creating a torrent file:

.. code-block:: python

   from torrent.torrent_creator import TorrentCreator
   from torrent.utils.config import TorrentConfig

   # Create a configuration with a tracker URL
   config = TorrentConfig(
       tracker_url="http://example.com/announce",
       private=True  # Optional: make the torrent private (default)
   )

   # Create a torrent creator
   creator = TorrentCreator(config)

   # Create a torrent file
   creator.create(
       input_path="path/to/content",
       output_path="output.torrent"
   )

Or using the command-line interface:

.. code-block:: bash

   # Create a private torrent (default)
   torrent-directories file path/to/content http://tracker.example.com/announce

   # Process multiple directories
   torrent-directories batch path/to/parent http://tracker.example.com/announce

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
