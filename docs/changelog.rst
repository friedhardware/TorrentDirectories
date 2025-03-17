Changelog
=========

[1.1.0] - 2025-03-17
====================



Changed
* Add Markdown version of changelog ([fff30f4])(https://github.com/friedhardware/TorrentDirectories/commit/fff30f4) (friedhardware)


Other
* test: Update release script tests to use version.py ([7e16b9a])(https://github.com/friedhardware/TorrentDirectories/commit/7e16b9a) (friedhardware)
* chore: Update release script for version.py and improved changelog handling ([127f120])(https://github.com/friedhardware/TorrentDirectories/commit/127f120) (friedhardware)
* chore: Update version to 1.1.0 and update changelog ([d16ac5d])(https://github.com/friedhardware/TorrentDirectories/commit/d16ac5d) (friedhardware)
All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[1.1.0] - 2024-03-17
=====================

Added
~~~~~
- Dedicated logging utilities module
- Improved empty file handling in batch processing
- Enhanced manifest management with force option
- Better type hints and code organization
- Additional test coverage

Changed
~~~~~~~
- Refactored logging setup into dedicated module
- Updated manifest handling to replace entries instead of appending when using --force
- Improved code organization and modularity
- Enhanced documentation

Fixed
~~~~~
- Empty file handling in batch processing
- Manifest entry replacement behavior
- Type hint issues across the codebase

[1.0.0] - 2024-03-XX
=====================

Initial release.

Added
~~~~~
- Basic torrent creation functionality
- Support for single files and directories
- Automatic piece size calculation
- Private torrent support
- Manifest management
- Command-line interface
- Batch processing support
- Comprehensive test suite
- Documentation
