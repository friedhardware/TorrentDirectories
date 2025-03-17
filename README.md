# TorrentDirectories

A Python tool for creating torrent files from directories with optimal settings and batch processing capabilities. Automatically calculates optimal piece sizes and supports both single file/directory and batch processing modes.

## Features

- ✨ Create torrents from single files or directories
- 🚀 Batch process multiple directories with resume support
- 🎯 Automatic optimal piece size calculation
- 🔒 Private torrents by default (with public option)
- 📝 Detailed logging and progress reporting
- 🔄 Resume support via manifest system
- ✅ Torrent verification after creation
- 🖥️ Cross-platform support (Windows, macOS, Linux)

## Table of Contents

- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Detailed Usage](#detailed-usage)
  - [Single File/Directory Mode](#single-filedirectory-mode)
  - [Batch Mode](#batch-mode)
  - [Common Options](#common-options)
  - [Error Handling](#error-handling)
- [Manifest System](#manifest-system)
- [Development](#development)
  - [Setting Up](#setting-up-development-environment)
  - [Running Tests](#running-tests)
  - [Code Style](#code-style)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

1. Install from source:
```bash
# Clone and enter directory
git clone https://github.com/friedhardware/TorrentDirectories.git
cd TorrentDirectories

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Unix/macOS
# Or on Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

2. Create a torrent from a single file or directory:
```bash
# Create a private torrent (default)
torrent-directories file path/to/content http://tracker.example.com/announce

# Specify output location
torrent-directories file path/to/content http://tracker.example.com/announce -o output.torrent

# Create a public torrent with metadata
torrent-directories file path/to/content http://tracker.example.com/announce \
    --public \
    --source "My Release Group" \
    --comment "Great content!"
```

3. Process multiple directories in batch mode:
```bash
# Process all subdirectories in a parent directory
torrent-directories batch path/to/parent http://tracker.example.com/announce

# Specify output directory for torrent files
torrent-directories batch path/to/parent http://tracker.example.com/announce -o path/to/torrents

# Process with custom settings
torrent-directories batch path/to/parent http://tracker.example.com/announce \
    --min-piece-size 1M \
    --max-piece-size 32M \
    --skip-empty \
    --force
```

## Requirements

- Python 3.13 or later
- libtorrent 2.0.0 or later
- click 8.1.3 or later

## Detailed Usage

### Single File/Directory Mode

Create a torrent from a single file or directory:

```bash
torrent-directories file <input_path> <tracker_url> [options]

# Examples:

# Basic usage - creates private torrent
torrent-directories file ./my_movie http://tracker.example.com/announce

# Specify output location
torrent-directories file ./my_movie http://tracker.example.com/announce -o my_movie.torrent

# Create public torrent with custom piece size and metadata
torrent-directories file ./my_movie http://tracker.example.com/announce \
    --public \
    --min-piece-size 1M \
    --max-piece-size 32M \
    --source "My Release Group" \
    --comment "Great content!"

# Skip empty files and include system files
torrent-directories file ./my_movie http://tracker.example.com/announce \
    --skip-empty \
    --include-system

# Preview changes without creating files (dry run)
torrent-directories --dry-run file ./my_movie http://tracker.example.com/announce
```

### Batch Mode

Process multiple subdirectories in a parent directory:

```bash
torrent-directories batch <parent_directory> <tracker_url> [options]

# Examples:

# Basic usage - process all subdirectories
torrent-directories batch ./movies http://tracker.example.com/announce

# Custom output directory and public torrents
torrent-directories batch ./movies http://tracker.example.com/announce \
    -o /path/to/torrents \
    --public

# Process with custom settings and force rebuild
torrent-directories batch ./movies http://tracker.example.com/announce \
    --min-piece-size 1M \
    --force \
    --include-system \
    --skip-empty

# Clean manifest and process directories with metadata
torrent-directories batch ./movies http://tracker.example.com/announce \
    --clean \
    --source "My Release Group" \
    --comment "Batch release"
```

### Common Options

- Global Options (before command):
  - `--version`: Show version information
  - `--verbose` or `-v`: Show detailed progress
  - `--dry-run`: Preview changes without making them
  - `--log-file FILE`: Write logs to file

- Torrent Options:
  - `--private | --public`: Set torrent privacy (mutually exclusive, private by default)
  - `--min-piece-size SIZE`: Minimum piece size (e.g., 16K, 1M, default: 256K)
  - `--max-piece-size SIZE`: Maximum piece size (e.g., 16M, 64M, default: 16M)
  - `--include-system`: Include system files (default: False)
  - `--skip-empty`: Skip empty files instead of failing (default: False)
  - `--force`: Overwrite existing torrents
  - `--source TEXT`: Add a source string to the torrent metadata
  - `--comment TEXT`: Add a comment to the torrent metadata
  - `-o/--output OUTPUT`: Output path for the torrent(s):
    - Single mode: Output file path (default: input name + .torrent)
    - Batch mode: Output directory (default: torrents/)

- Batch-specific Options:
  - `--clean`: Clean the manifest by removing missing entries
  - `--max-failures N`: Maximum failures before stopping (0 for unlimited)

### Error Handling

The tool handles various error conditions:

- Empty Files:
  - By default, attempting to create a torrent from an empty file will fail
  - Use `--skip-empty` to skip empty files instead of failing
  - In batch mode with `--skip-empty`, empty files are counted separately from other failures

- Existing Files:
  - By default, the tool won't overwrite existing torrent files
  - Use `--force` to overwrite existing files
  - In batch mode, `--force` also updates the manifest entries

- Maximum Failures:
  - In batch mode, use `--max-failures N` to stop after N failures
  - Empty files are only counted as failures if `--skip-empty` is not used
  - A value of 0 (default) means no limit

## Manifest System

The tool maintains a manifest file to track processed directories in batch mode. This enables:

- Skipping already processed directories
- Resuming interrupted batch operations
- Tracking which directories have been processed
- Automatic backup of the manifest before cleaning

The manifest is stored as a CSV file in the output directory with the following format:
```csv
directory_path,torrent_file,processed_at
"/path/to/movie1","movie1.torrent","2024-03-15T14:30:00"
```

The manifest system provides:
- Automatic skipping of already processed directories (unless `--force` is used)
- Cleaning of invalid entries with `--clean`
- Backup of the manifest before cleaning (saved as manifest.csv.bak)
- Thread-safe operations for concurrent access

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/friedhardware/TorrentDirectories.git
cd TorrentDirectories

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Unix/macOS
# Or on Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests with verbose output and coverage report
python -m pytest tests/ -v --cov=src/torrent

# Run only integration tests
python -m pytest tests/torrent/cli/test_commands_integration.py -v
```

### Code Style

The project uses several tools to maintain consistent code quality:

- Black for code formatting
- Ruff for linting and formatting
- isort for import sorting
- mypy for type checking

These tools are configured in `pyproject.toml` and run automatically via pre-commit hooks.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest tests/`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
