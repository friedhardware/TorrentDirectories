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
- 🛡️ Robust error handling with clear messages
- 📊 Type-safe progress reporting
- 🔍 Smart file existence checks
- 🧪 Comprehensive test coverage
- 🔐 Thread-safe operations
- 📈 Performance optimization
- 🔄 Automatic backup creation

## Table of Contents

- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Detailed Usage](#detailed-usage)
  - [Single File/Directory Mode](#single-filedirectory-mode)
  - [Batch Mode](#batch-mode)
  - [Common Options](#common-options)
  - [Error Handling](#error-handling)
- [Manifest System](#manifest-system)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
  - [Setting Up](#setting-up-development-environment)
  - [Running Tests](#running-tests)
  - [Code Style](#code-style)
  - [Documentation](#documentation)
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

# Process with custom settings and force rebuild
torrent-directories batch path/to/parent http://tracker.example.com/announce \
    --min-piece-size 1M \
    --max-piece-size 32M \
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
    --include-system

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

The tool handles various error conditions with clear messages and appropriate exit codes:

- **File Existence**:
  - Smart detection of existing files for both explicit and default paths
  - Clear error messages with instructions for using `--force`
  - Safe overwrite handling with proper backup

- **Progress Reporting**:
  - Type-safe progress calculations
  - Clear percentage and file count display
  - Real-time updates in verbose mode

- **Maximum Failures**:
  - In batch mode, use `--max-failures N` to stop after N failures
  - A value of 0 (default) means no limit

## Manifest System

The tool maintains a manifest file to track processed directories in batch mode. This enables:

- Skipping already processed directories
- Resuming interrupted batch operations
- Tracking which directories have been processed
- Automatic backup of the manifest before cleaning

The manifest is stored as a CSV file in the output directory with the following format:
```csv
"directory_path","torrent_file","processed_at"
"/path/to/movie1","movie1.torrent","2024-03-15T14:30:00"
"/path/to/movie2","movie2.torrent","2024-03-15T14:31:00"
```

The manifest system provides:
- Automatic skipping of already processed directories (unless `--force` is used)
- Cleaning of invalid entries with `--clean`
- Backup of the manifest before cleaning (saved as manifest.csv.bak_<timestamp>)
- Thread-safe operations for concurrent access

## Best Practices

For detailed best practices and advanced usage patterns, including:
- Directory organization strategies
- Piece size optimization for different content types
- Batch processing strategies
- Metadata best practices
- Error handling and recovery
- Automation tips
- Performance optimization
- Security considerations
- Testing guidelines
- Maintenance procedures

See our [Best Practices Guide](docs/best_practices.rst) in the documentation.

## Troubleshooting

### Common Issues


1. **File Already Exists**:
   ```
   Error: Output file already exists: path/to/output.torrent
   ```
   - **Solution**: Use `--force` to overwrite existing files

2. **Missing Torrent Files in Batch Mode**:
   ```
   Error: Found X missing torrent files.
   Use --clean to remove invalid entries from manifest.
   ```
   - **Solution**: Use `--clean` option to fix the manifest and recreate missing torrents

3. **Maximum Failures Reached**:
   ```
   Maximum failures reached
   Error: Failed to process directories
   ```
   - **Solution**: Fix the failing directories or use `--max-failures` to increase/remove the failure limit

### Best Practices

1. **Start with a Dry Run**:
   ```bash
   torrent-directories --dry-run batch ./movies http://tracker.example.com/announce
   ```
   This will show you what would be done without making any changes.

2. **Use Verbose Mode for Troubleshooting**:
   ```bash
   torrent-directories -v batch ./movies http://tracker.example.com/announce --log-file logs.txt
   ```
   The `-v` flag provides more information, and `--log-file` saves it to a file.

3. **Clean the Manifest When Needed**:
   - If you've manually deleted torrent files, use the `--clean` option to synchronize the manifest.

4. **Force Update When Content Changes**:
   - If you've updated the content in a directory, use `--force` to rebuild the torrents.

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

# Run specific test files
python -m pytest tests/torrent/cli/test_file_command.py -v
python -m pytest tests/torrent/cli/test_batch_command.py -v
```

### Code Style

The project uses several tools to maintain consistent code quality:
- `ruff` for linting
- `black` for code formatting
- `mypy` for type checking
- `pre-commit` hooks to automate checks

Run these tools before submitting changes:
```bash
ruff check .
black .
mypy src
```

### Documentation

The project uses Sphinx for documentation. The documentation source files are in the `docs/` directory.

#### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build HTML documentation
cd docs
make html

# Build PDF documentation (requires LaTeX)
make latexpdf

# Clean build directory
make clean
```

#### Writing Documentation

- API documentation is automatically generated from docstrings
- ReStructuredText (`.rst`) files in `docs/` contain manual documentation
- The documentation follows the NumPy docstring format

Key files:
- `docs/conf.py`: Sphinx configuration
- `docs/index.rst`: Documentation home page
- `docs/api/`: API reference documentation
- `docs/usage.rst`: Usage guide
- `docs/best_practices.rst`: Best practices guide

#### Documentation Standards

1. **API Documentation**:
   - Use NumPy style docstrings
   - Include type hints
   - Document exceptions
   - Provide usage examples

2. **RST Files**:
   - Use proper section hierarchy
   - Include cross-references
   - Add code examples where relevant
   - Keep formatting consistent

3. **Building and Testing**:
   - Build docs before committing changes
   - Check for Sphinx warnings
   - Verify all links work
   - Test code examples

Example docstring format:
```python
def create_torrent(path: str, tracker_url: str) -> None:
    """Create a torrent file from the given path.

    Parameters
    ----------
    path : str
        Path to the file or directory to create a torrent from.
    tracker_url : str
        URL of the tracker to use.

    Returns
    -------
    None

    Raises
    ------
    TorrentError
        If the torrent creation fails.
    ValueError
        If the path does not exist.

    Examples
    --------
    >>> create_torrent("path/to/file", "http://tracker.example.com/announce")
    """
```

## Contributing

Contributions are welcome! See the [Contributing Guide](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
