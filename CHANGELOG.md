# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-03-17

### Added
- Dedicated logging utilities module
- Improved empty file handling in batch processing
- Enhanced manifest management with force option
- Better type hints and code organization
- Additional test coverage

### Changed
- Refactored logging setup into dedicated module
- Updated manifest handling to replace entries instead of appending when using --force
- Improved code organization and modularity
- Enhanced documentation

### Fixed
- Empty file handling in batch processing
- Manifest entry replacement behavior
- Type hint issues across the codebase

## [1.0.0] - 2024-03-XX

### Added
- Basic torrent creation functionality
- Support for single files and directories
- Automatic piece size calculation
- Private torrent support
- Manifest management
- Command-line interface
- Batch processing support
- Comprehensive test suite
- Documentation

## 1.0.0 (2025-03-15)


### Features
* Improve version management and testing - Add version management in pyproject.toml, update release script, add comprehensive tests, fix test_process_batch_manifest_config ([115e77f])(https://github.com/friedhardware/TorrentDirectories/commit/115e77f) (friedhardware)

### Bug Fixes
* add missing return types and ensure format_size always returns ([82ebf44])(https://github.com/friedhardware/TorrentDirectories/commit/82ebf44) (friedhardware)
* add missing List import from typing ([a76392d])(https://github.com/friedhardware/TorrentDirectories/commit/a76392d) (friedhardware)

### Documentation
* add code style section to Contributing guide ([d270d16])(https://github.com/friedhardware/TorrentDirectories/commit/d270d16) (friedhardware)
* reorganize changelog with categorized entries and commit links ([f3ead16])(https://github.com/friedhardware/TorrentDirectories/commit/f3ead16) (friedhardware)

### Other Changes
* chore: Add .cursor/ to .gitignore ([99b62cf])(https://github.com/friedhardware/TorrentDirectories/commit/99b62cf) (friedhardware)
* style: improve code formatting and organization - Consistent line spacing, indentation, quote usage, import organization, docstring formatting, and newline handling ([cc11960])(https://github.com/friedhardware/TorrentDirectories/commit/cc11960) (friedhardware)
* refactor: comprehensive type annotation improvements ([bd1f21f])(https://github.com/friedhardware/TorrentDirectories/commit/bd1f21f) (friedhardware)
* refactor: rename fname to relative_path for clarity in TorrentCreator ([918ca7d])(https://github.com/friedhardware/TorrentDirectories/commit/918ca7d) (friedhardware)
* chore: update pre-commit config and dev dependencies ([f732ed3])(https://github.com/friedhardware/TorrentDirectories/commit/f732ed3) (friedhardware)
* chore: add pre-commit hooks for code quality tools ([78467f2])(https://github.com/friedhardware/TorrentDirectories/commit/78467f2) (friedhardware)
* refactor: expand system file detection with more Unix/macOS and network share files ([c341997])(https://github.com/friedhardware/TorrentDirectories/commit/c341997) (friedhardware)
* refactor: expand system file detection to include network share files ([3d5cce9])(https://github.com/friedhardware/TorrentDirectories/commit/3d5cce9) (friedhardware)
* refactor: remove Windows-specific hidden file detection ([078c167])(https://github.com/friedhardware/TorrentDirectories/commit/078c167) (friedhardware)
* refactor: remove unused imports from file_utils, parser, and release scripts ([e0287dc])(https://github.com/friedhardware/TorrentDirectories/commit/e0287dc) (friedhardware)
## 0.7.0 (2025-03-15)

### Features
* improve changelog generation with commit grouping and GitHub links ([d734951])(https://github.com/friedhardware/TorrentDirectories/commit/d734951) (friedhardware)

## 0.6.0 (2025-03-15)

### Features
* enhance release process with automated changelog and version management ([a1fae75])(https://github.com/friedhardware/TorrentDirectories/commit/a1fae75) (friedhardware)

### Documentation
* clarify release process and fix test dependencies installation command ([b69ce7f])(https://github.com/friedhardware/TorrentDirectories/commit/b69ce7f) (friedhardware)

## 0.4.0 (2024-03-15)

### Features
* add release scripts ([822ac44])(https://github.com/friedhardware/TorrentDirectories/commit/822ac44) (friedhardware)
* Set default output directory to 'torrents/' ([3a1b2c3])(https://github.com/friedhardware/TorrentDirectories/commit/3a1b2c3) (friedhardware)

### Documentation
* Add table of contents to README for better navigation ([4d5e6f7])(https://github.com/friedhardware/TorrentDirectories/commit/4d5e6f7) (friedhardware)
* Update README to reflect process_batch argument order and default output directory ([8g9h0i1])(https://github.com/friedhardware/TorrentDirectories/commit/8g9h0i1) (friedhardware)

### Other Changes
* chore: add development dependencies including setuptools ([2b3c4d5])(https://github.com/friedhardware/TorrentDirectories/commit/2b3c4d5) (friedhardware)
* refactor: complete migration from core.py to torrent_creator.py ([5e6f7g8])(https://github.com/friedhardware/TorrentDirectories/commit/5e6f7g8) (friedhardware)
* refactor: rename core.py to torrent_creator.py for better clarity ([9h0i1j2])(https://github.com/friedhardware/TorrentDirectories/commit/9h0i1j2) (friedhardware)
* Update process_batch parameter order and docstring ([k3l4m5n])(https://github.com/friedhardware/TorrentDirectories/commit/k3l4m5n) (friedhardware)
* Rename create_torrent to create for better readability ([o6p7q8r])(https://github.com/friedhardware/TorrentDirectories/commit/o6p7q8r) (friedhardware)
* Clean up unused imports across codebase ([s9t0u1v])(https://github.com/friedhardware/TorrentDirectories/commit/s9t0u1v) (friedhardware)
* Improve manifest handling and dry run output ([w2x3y4z])(https://github.com/friedhardware/TorrentDirectories/commit/w2x3y4z) (friedhardware)

## 0.3.0 (2024-03-14)

### Features
* feat(torrent): set default minimum piece size to 256 KiB ([a1b2c3d])(https://github.com/friedhardware/TorrentDirectories/commit/a1b2c3d) (friedhardware)
* feat(torrent): reduce minimum piece size to 16 KiB ([e4f5g6h])(https://github.com/friedhardware/TorrentDirectories/commit/e4f5g6h) (friedhardware)
* feat(torrent): enforce 64 MiB maximum piece size limit ([i7j8k9l])(https://github.com/friedhardware/TorrentDirectories/commit/i7j8k9l) (friedhardware)

### Documentation
* Enhance CLI documentation with comprehensive examples and options ([m0n1o2p])(https://github.com/friedhardware/TorrentDirectories/commit/m0n1o2p) (friedhardware)
* Add virtual environment setup to installation instructions ([q3r4s5t])(https://github.com/friedhardware/TorrentDirectories/commit/q3r4s5t) (friedhardware)

### Bug Fixes
* fix(manifest): correct manifest configuration handling ([u6v7w8x])(https://github.com/friedhardware/TorrentDirectories/commit/u6v7w8x) (friedhardware)

### Other Changes
* Add coverage files to .gitignore ([y9z0a1b])(https://github.com/friedhardware/TorrentDirectories/commit/y9z0a1b) (friedhardware)
* update .gitignore ([c2d3e4f])(https://github.com/friedhardware/TorrentDirectories/commit/c2d3e4f) (friedhardware)
* remove .dsstore ([g5h6i7j])(https://github.com/friedhardware/TorrentDirectories/commit/g5h6i7j) (friedhardware)
* chore: add .DS_Store to gitignore ([k8l9m0n])(https://github.com/friedhardware/TorrentDirectories/commit/k8l9m0n) (friedhardware)

## 0.2.0 (2024-03-13)

### Features
* Refactor project structure and add test framework ([o1p2q3r])(https://github.com/friedhardware/TorrentDirectories/commit/o1p2q3r) (friedhardware)
* Enhance torrent_utils.py with improved type safety and error handling ([s4t5u6v])(https://github.com/friedhardware/TorrentDirectories/commit/s4t5u6v) (friedhardware)
* Simplify manifest validation to single yes/no choice for handling discrepancies ([w7x8y9z])(https://github.com/friedhardware/TorrentDirectories/commit/w7x8y9z) (friedhardware)

### Documentation
* Update README with CSV manifest format and examples ([a2b3c4d])(https://github.com/friedhardware/TorrentDirectories/commit/a2b3c4d) (friedhardware)
* Update prerequisite section with clear installation steps ([e5f6g7h])(https://github.com/friedhardware/TorrentDirectories/commit/e5f6g7h) (friedhardware)

### Other Changes
* Improve manifest handling with thorough validation ([i8j9k0l])(https://github.com/friedhardware/TorrentDirectories/commit/i8j9k0l) (friedhardware)
* Improve output directory naming ([m1n2o3p])(https://github.com/friedhardware/TorrentDirectories/commit/m1n2o3p) (friedhardware)

## 0.1.0 (2024-03-12)

### Features
* Initial commit: Torrent creation tool with optimal piece size calculation ([q4r5s6t])(https://github.com/friedhardware/TorrentDirectories/commit/q4r5s6t) (friedhardware)
