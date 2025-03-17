Installation
============

Requirements
----------------------

TorrentDirectories requires Python 3.8 or later and libtorrent 2.0.0 or later.

Installing from PyPI
----------------------

The recommended way to install TorrentDirectories is via pip:

.. code-block:: bash

   pip install torrent-directories

Installing from Source
----------------------

To install TorrentDirectories from source:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/friedhardware/TorrentDirectories.git
      cd TorrentDirectories

2. Create and activate a virtual environment (optional but recommended):

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

3. Install the package in development mode:

   .. code-block:: bash

      pip install -e .

Development Installation
----------------------

For development, you'll want to install additional dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

This will install additional packages needed for development:

* pytest
* pytest-cov
* pytest-mock
* black
* isort
* mypy
* ruff
* sphinx
* sphinx-rtd-theme 