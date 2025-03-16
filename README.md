# TorrentDirectories

A Python tool for creating torrent files from directories with optimal settings and batch processing capabilities.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [From Source](#from-source)
  - [Requirements](#requirements)
- [Usage](#usage)
  - [Command Structure](#command-structure)
  - [Global Options](#global-options)
  - [Commands](#commands)
    - [1. File Command](#1-file-command)
    - [2. Batch Command](#2-batch-command)
- [Manifest System](#manifest-system)
  - [Safety Features](#safety-features)
  - [File Format](#file-format)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
  - [TorrentCreator](#torrentcreator)
  - [ManifestManager](#manifestmanager)
- [Contributing](#contributing)
- [Release Process](#release-process)
- [License](#license)
- [Testing](#testing)

## Features

- Create torrents from single files or directories
- Batch process multiple directories with resume support
- Optimal piece size calculation:
  - Minimum piece size: 16 KiB (hard limit)
  - Maximum piece size: 64 MiB (hard limit)
  - Default: 256 KiB minimum, 16 MiB maximum piece size
  - Targets 1000-2000 pieces for optimal client performance
- Skip hidden and system files (configurable)
- Progress reporting and detailed logging
- Manifest system for tracking processed directories
- Torrent verification after creation
- Cross-platform support (Windows, macOS, Linux)
- Monitor directories for changes and update torrents
- Web interface for monitoring torrent status and controlling batch processes
- Dark mode UI for better visibility
- Real-time status updates and error reporting

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/friedhardware/TorrentDirectories.git
cd TorrentDirectories

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Unix/macOS
# Or on Windows:
# venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Requirements

- Python 3.7 or later
- libtorrent 2.0.0 or later

## Usage

The tool can be run either as an installed command or as a Python module:

```bash
# As an installed command
torrent-directories [command] [options]

# As a Python module
python -m torrent.cli [command] [options]
```

### Command Structure

The general command structure is:
```bash
torrent-directories [global options] <command> [command options] <required arguments>
```

### Global Options

These options work with all commands and must be specified before the command:

```bash
# Show program version
torrent-directories --version

# Enable verbose output (detailed logging)
torrent-directories -v [command] [args]
# or
torrent-directories --verbose [command] [args]

# Write logs to a file
torrent-directories --log-file path/to/log.txt [command] [args]

# Preview changes without making them (dry run)
torrent-directories --dry-run [command] [args]
```

### Commands

The tool supports two main commands: `file` and `batch`

#### 1. File Command

The `file` command creates a torrent from a single file or directory.

Syntax:
```bash
torrent-directories file [options] <input_path> <tracker_url>
```

Required arguments:
- `input_path`: Path to the file or directory to create a torrent from
- `tracker_url`: URL of the tracker to include in the torrent

Options:
```bash
# Specify custom output path (default: input_name.torrent)
-o, --output PATH          # Example: -o /torrents/movie.torrent

# Force overwrite if output file exists
--force                    # Example: --force

# Custom piece sizes (accepts K, M suffixes)
--min-piece-size SIZE     # Example: --min-piece-size 32K (minimum: 16K)
--max-piece-size SIZE     # Example: --max-piece-size 32M (maximum: 64M)

# Custom target piece count range
--target-pieces RANGE     # Example: --target-pieces 1000-2000

# Include normally skipped files
--include-hidden          # Include hidden files/directories
--include-system          # Include system files
```

Examples:
```bash
# Basic usage - create torrent in current directory
torrent-directories file ./my_movie http://tracker.example.com/announce

# Specify custom output location
torrent-directories file -o /torrents/my_movie.torrent ./my_movie http://tracker.example.com/announce

# Force overwrite existing torrent with custom piece size
torrent-directories file --force --min-piece-size 1M --max-piece-size 32M \
    -o /torrents/my_movie.torrent ./my_movie http://tracker.example.com/announce

# Include hidden files with verbose output
torrent-directories -v file --include-hidden \
    ./my_movie http://tracker.example.com/announce

# Preview torrent creation with all options
torrent-directories --dry-run file \
    --min-piece-size 256K \
    --max-piece-size 16M \
    --target-pieces 1500-2000 \
    --include-hidden \
    --include-system \
    -o /torrents/my_movie.torrent \
    ./my_movie \
    http://tracker.example.com/announce
```

#### 2. Batch Command

The `batch` command processes multiple subdirectories in a parent directory.

Syntax:
```bash
torrent-directories batch [options] <parent_directory> <tracker_url>
```

Required arguments:
- `parent_directory`: Directory containing subdirectories to process
- `tracker_url`: URL of the tracker to include in all torrents

Options:
```bash
# Specify output directory for torrent files and manifest (defaults to 'torrents/')
-o, --output PATH        # Example: -o /path/to/output

# Preview changes without making them
--dry-run               # Example: --dry-run

# Clean manifest of missing entries before processing
--clean                 # Example: --clean

# Force rebuild existing torrents
--force                 # Example: --force

# Stop processing after N failures (0 = unlimited)
--max-failures N        # Example: --max-failures 3

# All torrent creation options from file command also work:
--min-piece-size SIZE   # Example: --min-piece-size 256K
--max-piece-size SIZE   # Example: --max-piece-size 16M
--target-pieces RANGE   # Example: --target-pieces 1000-2000
--include-hidden
--include-system
```

Examples:
```bash
# Basic usage - process all subdirectories (output to 'torrents/' directory)
torrent-directories batch ./movies http://tracker.example.com/announce

# Use custom output directory and force rebuild
torrent-directories batch \
    -o /path/to/output \
    --force \
    --min-piece-size 1M \
    --include-hidden \
    ./movies \
    http://tracker.example.com/announce

# Process with failure limit and custom piece count
torrent-directories batch \
    -o /path/to/output \
    --max-failures 5 \
    --target-pieces 1000-2000 \
    ./movies \
    http://tracker.example.com/announce
```

## Manifest System

The manifest system tracks processed directories to prevent duplicate processing and enable resume functionality.

### Safety Features

- Automatic backup of manifest file before modifications
- Validation of manifest entries against actual torrent files
- Configurable validation behavior through environment variables
- CSV format for easy inspection and manual editing
- Skip functionality for already processed directories

### File Format

The manifest is a CSV file with three fields:
```csv
directory_path,torrent_file,processed_at
"/path/to/movie1","movie1.torrent","2024-03-15T14:30:00"
```

- `directory_path`: Absolute path to processed directory
- `torrent_file`: Name of created torrent file
- `processed_at`: ISO 8601 timestamp of processing

The file is created in the output directory (`torrents/` by default) and updated after each successful torrent creation.

## Project Structure

```
TorrentDirectories/
├── src/
│   └── torrent/
│       ├── cli/                    # Command-line interface
│       │   ├── commands.py         # Command implementations
│       │   ├── config.py           # Configuration management
│       │   ├── main.py             # Main entry point
│       │   └── parser.py           # Argument parsing
│       ├── utils/                  # Utility functions
│       │   ├── config.py           # Configuration utilities
│       │   └── file_utils.py       # File handling utilities
│       ├── manifest.py             # Manifest system
│       └── torrent_creator.py      # Core torrent creation
├── tests/                          # Test suite
├── scripts/                        # Utility scripts
├── README.md                       # This file
├── CHANGELOG.md                    # Version history
├── LICENSE                         # MIT License
├── pyproject.toml                  # Project metadata
└── setup.py                       # Package setup
```

## API Reference

### TorrentCreator

The main class for creating torrent files.

```python
from torrent import TorrentCreator

creator = TorrentCreator(
    min_piece_size="256K",
    max_piece_size="16M",
    target_pieces=(1000, 2000),
    include_hidden=False,
    include_system=False
)

# Create a torrent from a directory
creator.create(
    input_path="/path/to/directory",
    tracker_url="http://tracker.example.com/announce",
    output_path="output.torrent"
)
```

### ManifestManager

Manages the manifest system for tracking processed directories.

```python
from torrent import ManifestManager

# Create with custom configuration
config = ManifestConfig(
    filename="custom_manifest.csv",
    encoding="utf-8"
)

# Check if a directory has been processed
is_processed = manifest.is_directory_processed(directory_path)

# Mark a directory as processed
manifest.mark_directory_processed(directory_path, torrent_path)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Code Style

The project uses several tools to maintain consistent code quality:

- [Black](https://github.com/psf/black) for code formatting
- [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- [isort](https://github.com/pycqa/isort) for import sorting
- [mypy](https://github.com/python/mypy) for type checking

These tools are configured in `pyproject.toml` and run automatically via pre-commit hooks. To set up your development environment:

```bash
# Install pre-commit hooks
pre-commit install

# Run all checks manually
pre-commit run --all-files
```

## Release Process

The project uses semantic versioning (MAJOR.MINOR.PATCH) with a single source of truth in `src/torrent/__init__.py`. The release process is automated using `scripts/release.py`.

### Making a Release

The project uses semantic versioning (MAJOR.MINOR.PATCH) with a single source of truth in `src/torrent/__init__.py`. The release process is automated using `scripts/release.py`.

To create a new release:

1. Ensure your working directory is clean:
   ```bash
   git status  # Should show no uncommitted changes
   ```

2. Choose your release type and run the release script:
   ```bash
   # For a new feature release (increments minor version)
   python scripts/release.py

   # For a breaking change (increments major version)
   python scripts/release.py --bump major

   # For a bug fix (increments patch version)
   python scripts/release.py --bump patch

   # For a specific version (e.g., for a hotfix)
   python scripts/release.py --version 0.4.0
   ```

The release script will:
- Run the test suite
- Update version in all files (setup.py, pyproject.toml)
- Create a git tag
- Build and test the package
- Create a release commit
- Append new changes to CHANGELOG.md from git commit history since last tag
- Push changes and tags to the remote repository

Optional flags:
```bash
--no-tests    # Skip running tests
--no-publish  # Skip publishing to PyPI
```

After the release:
1. Review the changes in CHANGELOG.md
2. Create a GitHub release with the new tag
3. Update any documentation or website content

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Testing

The project uses pytest for testing. To run the tests:

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage report
pytest --cov=torrent

# Run tests with verbose output
pytest -v

# Run tests and show local variables on failure
pytest --showlocals
```

## Basic Commands

```bash
# Create a torrent from a directory
torrent create /path/to/directory

# Process multiple directories in batch mode
torrent batch /path/to/directories/*

# Run the torrent client with web interface
torrent client --web
```

## Web Interface

The web interface provides a modern, dark-mode UI for monitoring and controlling the torrent client. To enable it, use the `--web` flag when starting the client:

```bash
torrent client --web --web-port 5000
```

The web interface includes:

- Real-time torrent status monitoring
- Batch process controls (start/stop)
- Statistics dashboard
- Error reporting
- Dark mode UI for better visibility

#### Web Interface Features

1. **Torrent Status**
   - List of active torrents
   - Seeding/downloading status
   - Progress indicators
   - Upload/download rates

2. **Batch Process Controls**
   - Start/stop batch processing
   - Status monitoring
   - Last run time
   - Next scheduled check

3. **Statistics Dashboard**
   - Total torrents
   - Seeding count
   - Downloading count
   - Error count

4. **Error Reporting**
   - Recent error messages
   - Status indicators
   - Error history

### Configuration

The client can be configured using command-line arguments:

```bash
torrent client \
    --torrent-dir /path/to/torrents \
    --data-dir /path/to/data \
    --port 6881 \
    --max-upload-rate 1000 \
    --max-download-rate 1000 \
    --max-connections 200 \
    --check-interval 60 \
    --auto-restart \
    --web \
    --web-port 5000
```

#### Batch Process Options

When using the client with batch processing, you can configure:

```bash
torrent client \
    --batch-check-interval 300 \
    --batch-max-failures 3 \
    --batch-clean \
    --batch-force \
    --batch-dry-run
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
# Format code
black .

# Sort imports
isort .

# Run linter
flake8
```
