.. TorrentDirectories documentation master file, created by
   sphinx-quickstart on Sun Mar 16 19:24:41 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TorrentDirectories's documentation!
==============================================

TorrentDirectories is a Python library for creating and managing torrent files with optimal settings. It provides a simple interface for creating torrent files from both single files and directories, with features like automatic piece size calculation and torrent verification.

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

* Create torrent files from single files or directories
* Automatic optimal piece size calculation
* Torrent file verification
* Support for private torrents
* Clean manifest management
* Command-line interface

Installation
------------

You can install TorrentDirectories using pip:

.. code-block:: bash

   pip install torrentdirectories

Quick Start
==========

Here's a simple example of creating a torrent file:

.. code-block:: python

   from torrent.torrent_creator import TorrentCreator
   from torrent.utils.config import TorrentConfig

   # Create a configuration
   config = TorrentConfig(tracker_url="http://example.com/announce")

   # Create a torrent creator
   creator = TorrentCreator(config)

   # Create a torrent file
   creator.create("path/to/file", "output.torrent")

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

