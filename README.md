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

# Create a public torrent
torrent-directories file path/to/content http://tracker.example.com/announce --public
```

3. Process multiple directories in batch mode:
```bash
# Process all subdirectories in a parent directory
torrent-directories batch path/to/parent http://tracker.example.com/announce

# Specify output directory for torrent files
torrent-directories batch path/to/parent http://tracker.example.com/announce -o path/to/torrents
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

# Create public torrent with custom piece size
torrent-directories file ./my_movie http://tracker.example.com/announce \
    --public \
    --min-piece-size 1M \
    --max-piece-size 32M

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
    --include-system

# Clean manifest and process directories
torrent-directories batch ./movies http://tracker.example.com/announce --clean
```

### Common Options

- Global Options (before command):
  - `--version`: Show version information
  - `--verbose` or `-v`: Show detailed progress
  - `--dry-run`: Preview changes without making them
  - `--log-file FILE`: Write logs to file

- Torrent Options:
  - `--private | --public`: Set torrent privacy (mutually exclusive, private by default)
  - `--min-piece-size SIZE`: Minimum piece size (e.g., 16K, 1M)
  - `--max-piece-size SIZE`: Maximum piece size (e.g., 16M, 64M)
  - `--target-pieces MIN-MAX`: Target piece count range (e.g., 1000-2000)
  - `--include-system`: Include system files
  - `--force`: Overwrite existing torrents
  - `-o/--output OUTPUT`: Output path for the torrent(s):
    - Single mode: Output file path (default: input name + .torrent)
    - Batch mode: Output directory (default: torrents/)

- Batch-specific Options:
  - `--clean`: Clean the manifest by removing missing entries
  - `--max-failures N`: Maximum failures before stopping (0 for unlimited)

## Manifest System

The tool maintains a manifest file to track processed directories in batch mode. This enables:

- Skipping already processed directories
- Resuming interrupted batch operations
- Tracking which directories have been processed

The manifest is stored as a CSV file in the output directory with the following format:
```csv
directory_path,torrent_file,processed_at
"/path/to/movie1","movie1.torrent","2024-03-15T14:30:00"
```

To clean up the manifest and remove entries for missing torrents:
```bash
torrent-directories batch ./movies http://tracker.example.com/announce --clean
```

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
