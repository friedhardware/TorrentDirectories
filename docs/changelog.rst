Changelog
=========

[1.3.0] - 2025-03-17
===================

[1.2.0] - 2025-03-17
===================

Fixed
-----
* update release script to push commits before tags and update Python version requirement ([71f2dcd])(https://github.com/friedhardware/TorrentDirectories/commit/71f2dcd) (friedhardware)

[1.1.1] - 2025-03-17
===================

Changed
-------
* Update documentation to match implementation and add missing options ([b29a287])(https://github.com/friedhardware/TorrentDirectories/commit/b29a287) (friedhardware)

[1.1.0] - 2025-03-17
===================

Changed
-------
* Add Markdown version of changelog ([fff30f4])(https://github.com/friedhardware/TorrentDirectories/commit/fff30f4) (friedhardware)
* Improve code organization and test coverage - Move logging setup to dedicated module, fix empty file handling, update manifest handling, add type hints, update docs ([870b411])(https://github.com/friedhardware/TorrentDirectories/commit/870b411) (friedhardware)
* update documentation to match actual implementation ([4e3dcca])(https://github.com/friedhardware/TorrentDirectories/commit/4e3dcca) (friedhardware)

Other
-----
* chore: Release version 1.1.0 ([08caf59])(https://github.com/friedhardware/TorrentDirectories/commit/08caf59) (friedhardware)
* test: Update release script tests to use version.py ([7e16b9a])(https://github.com/friedhardware/TorrentDirectories/commit/7e16b9a) (friedhardware)
* chore: Update release script for version.py and improved changelog handling ([127f120])(https://github.com/friedhardware/TorrentDirectories/commit/127f120) (friedhardware)
* chore: Update version to 1.1.0 and update changelog ([d16ac5d])(https://github.com/friedhardware/TorrentDirectories/commit/d16ac5d) (friedhardware)
* Update documentation heading levels for better navigation hierarchy ([329304e])(https://github.com/friedhardware/TorrentDirectories/commit/329304e) (friedhardware)
* Fix documentation warnings and improve RST formatting ([6c13bca])(https://github.com/friedhardware/TorrentDirectories/commit/6c13bca) (friedhardware)
* Update .gitignore and add .cursorignore ([b0358f6])(https://github.com/friedhardware/TorrentDirectories/commit/b0358f6) (friedhardware)
* Add documentation styling and favicon ([e9bba2a])(https://github.com/friedhardware/TorrentDirectories/commit/e9bba2a) (friedhardware)
* Update GitHub Pages configuration ([e8754ac])(https://github.com/friedhardware/TorrentDirectories/commit/e8754ac) (friedhardware)
* Add Sphinx documentation and GitHub workflow for docs ([0083883])(https://github.com/friedhardware/TorrentDirectories/commit/0083883) (friedhardware)
* fix(manifest): improve concurrency handling and cache updates ([d187700])(https://github.com/friedhardware/TorrentDirectories/commit/d187700) (friedhardware)
* refactor(ManifestCache): improve error handling and state management ([805c6bf])(https://github.com/friedhardware/TorrentDirectories/commit/805c6bf) (friedhardware)

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[1.1.0] - 2024-03-17
===================

Added
-----
- Dedicated logging utilities module
- Improved empty file handling in batch processing
- Enhanced manifest management with force option
- Better type hints and code organization
- Additional test coverage

Changed
-------
- Refactored logging setup into dedicated module
- Updated manifest handling to replace entries instead of appending when using --force
- Improved code organization and modularity
- Enhanced documentation

Fixed
-----
- Empty file handling in batch processing
- Manifest entry replacement behavior
- Type hint issues across the codebase

[1.0.0] - 2024-03-XX
===================

Initial release.

Added
-----
- Basic torrent creation functionality
- Support for single files and directories
- Automatic piece size calculation
- Private torrent support
- Manifest management
- Command-line interface
- Batch processing support
- Comprehensive test suite
- Documentation
