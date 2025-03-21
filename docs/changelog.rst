Changelog
=========

[1.4.2] - 2025-03-21
====================



Added
* Implement interrupt handling for CLI operations ([ab1d68c])(https://github.com/friedhardware/TorrentDirectories/commit/ab1d68c) (friedhardware)
* Implement interrupt handling for CLI operations ([90d2e01])(https://github.com/friedhardware/TorrentDirectories/commit/90d2e01) (friedhardware)
[1.4.1] - 2025-03-21
====================



Changed
*  improve code quality, testing, and documentation ([0fb3cf5])(https://github.com/friedhardware/TorrentDirectories/commit/0fb3cf5) (friedhardware)


Fixed
* update error code consistency test to explicitly specify output file ([3466d0e])(https://github.com/friedhardware/TorrentDirectories/commit/3466d0e) (friedhardware)
[1.4.0] - 2025-03-20
====================



Changed
* add comprehensive best practices guide and update documentation ([87f2296])(https://github.com/friedhardware/TorrentDirectories/commit/87f2296) (friedhardware)
*  simplify logging and improve test output handling * Remove log_and_echo function in favor of direct click.echo calls * Update integration tests to use direct function calls instead of Click runner * Fix black formatting in commands.py ([c7ffc42])(https://github.com/friedhardware/TorrentDirectories/commit/c7ffc42) (friedhardware)
* simplify changelog structure and fix heading underlines ([c61e8c0])(https://github.com/friedhardware/TorrentDirectories/commit/c61e8c0) (friedhardware)
* update changelog to use toctree for table of contents control ([b2daccf])(https://github.com/friedhardware/TorrentDirectories/commit/b2daccf) (friedhardware)
* adjust changelog heading levels and move tocdepth directive ([4a060ca])(https://github.com/friedhardware/TorrentDirectories/commit/4a060ca) (friedhardware)
* update changelog headings to show in table of contents ([69b424d])(https://github.com/friedhardware/TorrentDirectories/commit/69b424d) (friedhardware)
* update changelog to use rubric directives for version headings ([923413b])(https://github.com/friedhardware/TorrentDirectories/commit/923413b) (friedhardware)
* hide version headings from table of contents ([ac45cce])(https://github.com/friedhardware/TorrentDirectories/commit/ac45cce) (friedhardware)
* standardize changelog heading levels and formatting ([2257ad1])(https://github.com/friedhardware/TorrentDirectories/commit/2257ad1) (friedhardware)
*  make PyPI publishing opt-in with --publish flag ([8fac6fc])(https://github.com/friedhardware/TorrentDirectories/commit/8fac6fc) (friedhardware)


Fixed
* improve file existence checks and type safety ([6c2f0ad])(https://github.com/friedhardware/TorrentDirectories/commit/6c2f0ad) (friedhardware)


Other
* chore: remove test artifacts from manual testing * Remove test_empty_batch directory and its contents * Remove torrents/manifest.csv ([dd8882f])(https://github.com/friedhardware/TorrentDirectories/commit/dd8882f) (friedhardware)
* chore: remove generated docs from git tracking ([821b20e])(https://github.com/friedhardware/TorrentDirectories/commit/821b20e) (friedhardware)
.. _changelog:

[1.3.0] - 2025-03-17
--------------------

Fixed
~~~~~
* Improved file existence checking in single file mode to handle both explicit and default output paths
* Fixed type safety issues in progress reporting and batch command handling
* Enhanced error handling for file existence checks
* Improved type annotations throughout the codebase

Changed
~~~~~~~
* Refactored progress reporting to use proper type annotations
* Enhanced test coverage for file existence scenarios
* Improved code organization in utils modules

[1.2.0] - 2025-03-17
--------------------

Fixed
~~~~~
* update release script to push commits before tags and update Python version requirement ([71f2dcd])(https://github.com/friedhardware/TorrentDirectories/commit/71f2dcd) (friedhardware)

[1.1.1] - 2025-03-17
--------------------

Changed
~~~~~~~
* Update documentation to match implementation and add missing options ([b29a287])(https://github.com/friedhardware/TorrentDirectories/commit/b29a287) (friedhardware)

[1.1.0] - 2025-03-17
--------------------

Changed
~~~~~~~
* Add Markdown version of changelog ([fff30f4])(https://github.com/friedhardware/TorrentDirectories/commit/fff30f4) (friedhardware)
* Improve code organization and test coverage - Move logging setup to dedicated module, fix empty file handling, update manifest handling, add type hints, update docs ([870b411])(https://github.com/friedhardware/TorrentDirectories/commit/870b411) (friedhardware)
* update documentation to match actual implementation ([4e3dcca])(https://github.com/friedhardware/TorrentDirectories/commit/4e3dcca) (friedhardware)

Other
~~~~~
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
--------------------

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
--------------------

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
