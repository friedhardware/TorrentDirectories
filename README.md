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
  - [Environment Variables](#environment-variables)
- [Manifest System](#manifest-system)
  - [Safety Features](#safety-features)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
  - [TorrentCreator](#torrentcreator)
  - [ManifestManager](#manifestmanager)
- [Contributing](#contributing)
- [License](#license)
- [Testing](#testing)
  - [Setting Up the Test Environment](#setting-up-the-test-environment)
  - [Running Tests](#running-tests)
  - [Test Categories](#test-categories)
  - [Test Structure](#test-structure)
  - [Fixtures](#fixtures)
  - [Test Configuration](#test-configuration)
  - [Writing Tests](#writing-tests)
  - [Coverage Reports](#coverage-reports)
  - [Debugging Tests](#debugging-tests)

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
- pywin32 (Windows only)

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

# Use custom output directory for all files
torrent-directories batch \
    -o /path/to/output \
    ./movies \
    http://tracker.example.com/announce

# Preview changes with custom output directory
torrent-directories batch \
    --dry-run \
    -o /path/to/output \
    ./movies \
    http://tracker.example.com/announce

# Clean manifest and force rebuild with custom settings
torrent-directories batch \
    -o /path/to/output \
    --clean \
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

### Environment Variables

The tool also supports configuration through environment variables:

```bash
# Set default piece sizes (16K minimum, 64M maximum)
export TORRENT_MIN_PIECE_SIZE=16K
export TORRENT_MAX_PIECE_SIZE=16M  # Default, can be increased up to 64M

# Configure file handling
export TORRENT_SKIP_HIDDEN=0     # Include hidden files
export TORRENT_SKIP_SYSTEM=0     # Include system files
```

## Manifest System

The tool maintains a CSV manifest file to track processed directories. The manifest file is named `manifest.csv` and is stored in:
- The 'torrents/' directory by default
- The specified output directory when using `-o/--output`

The manifest file format is:

```csv
directory_path,torrent_file,processed_at
/path/to/movie1,movie1.torrent,2024-03-15T14:30:00
/path/to/movie2,movie2.torrent,2024-03-15T14:35:00
```

When using the batch command:
1. All torrent files are created in the output directory ('torrents/' by default)
2. The manifest file is stored in the same directory as the torrent files

### Safety Features

- Append-only writes for data integrity
- Immediate entry recording after successful torrent creation
- Header validation on file load
- Backup creation before modifications
- Output directory creation if it doesn't exist
- Validation states:
  1. Fresh start (no manifest)
  2. Perfect match (all torrents exist)
  3. Discrepancies found (missing torrents)

## Project Structure

```
TorrentDirectories/
├── src/
│   ├── torrent/
│   │   ├── core.py       # Core torrent creation
│   │   ├── manifest.py   # Manifest management
│   │   └── cli.py        # Command-line interface
│   └── utils/
│       ├── config.py     # Configuration classes
│       └── file_utils.py # File system utilities
├── tests/               # Test modules
├── setup.py            # Package configuration
└── README.md          # Documentation
```

## API Reference

### TorrentCreator

```python
from torrent import TorrentCreator

# Create with custom configuration
config = TorrentConfig(
    min_piece_size=1024 * 1024,  # 1 MiB
    max_piece_size=16 * 1024 * 1024,  # 16 MiB
    skip_hidden=True,
    skip_system_files=True
)

torrent_creator = TorrentCreator(tracker_url, config)
torrent_path = torrent_creator.create(input_path, output_path=None)
```

### ManifestManager

```python
from torrent import ManifestManager

# Create with custom configuration
config = ManifestConfig(
    filename="custom_manifest.csv",
    encoding="utf-8"
)

manifest = ManifestManager(config)

# Track new torrent
manifest.add_entry(directory_path, torrent_file)

# Find missing torrents
missing = manifest.get_missing_torrents()

# Clean invalid entries
manifest.clean_manifest(output_dir)

# Check if directory was processed
is_processed = manifest.is_directory_processed(directory_path)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Testing

The project uses pytest for testing and includes a comprehensive test suite with fixtures and configuration for different test scenarios.

### Setting Up the Test Environment

1. Install test dependencies:
```bash
# Install all development dependencies
pip install -e ".[dev]"

# Or install specific test requirements
pip install pytest pytest-cov pytest-mock
```

2. Install optional dependencies for specific tests:
```bash
# For Windows-specific tests
pip install pywin32  # Windows only

# For integration tests
pip install requests  # For tracker communication tests
```

3. Configure environment variables (optional):
```bash
# Set test tracker URL (for integration tests)
export TEST_TRACKER_URL="http://localhost:6969/announce"

# Set test data directory (for integration tests)
export TEST_DATA_DIR="/path/to/test/data"
```

4. Verify the test environment:
```bash
# Check pytest installation and plugins
pytest --version

# List available markers
pytest --markers

# Show test collection without running
pytest --collect-only
```

#### Development Setup

For development, we recommend setting up a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate it (Unix/macOS)
source venv/bin/activate

# Activate it (Windows)
venv\Scripts\activate

# Install in development mode with test dependencies
pip install -e ".[dev]"
```

#### IDE Integration

For VS Code users, add these settings to `.vscode/settings.json`:
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests",
        "-v",
        "--tb=short"
    ]
}
```

For PyCharm users:
1. Go to Settings → Tools → Python Integrated Tools
2. Set Default Test Runner to "pytest"
3. Configure pytest options in Run/Debug Configurations

#### Pre-commit Hooks

We recommend setting up pre-commit hooks to ensure tests pass before committing:

1. Install pre-commit:
```bash
pip install pre-commit
```

2. Create `.pre-commit-config.yaml`:
```yaml
repos:
-   repo: local
    hooks:
    -   id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
```

3. Install the hooks:
```bash
pre-commit install
```

### Running Tests

Basic test execution:
```bash
# Run all tests
pytest

# Run with detailed output
pytest -v

# Run and show test coverage
pytest --cov

# Run specific test file
pytest tests/torrent/cli/test_commands.py
```

### Test Categories

Tests are automatically categorized using markers:

```bash
# Run only CLI tests
pytest -m cli

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Test Structure

The test suite is organized to mirror the source code structure:

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── torrent/
│   ├── cli/             # CLI-related tests
│   │   ├── test_parser.py
│   │   ├── test_config.py
│   │   ├── test_commands.py
│   │   └── test_main.py
│   ├── test_core.py     # Core functionality tests
│   └── test_manifest.py # Manifest handling tests
└── utils/               # Utility function tests
```

### Fixtures

The test suite provides several reusable fixtures:

- `temp_dir`: Creates a temporary directory that's automatically cleaned up
- `sample_files`: Provides a sample directory structure with various file types
- `default_config`: Default TorrentConfig instance
- `manifest_config`: ManifestConfig with temporary file
- `clean_env`: Cleans environment variables that might affect tests
- `assert_logs`: Enhanced logging assertions

Example usage:
```python
def test_something(sample_files, clean_env, assert_logs):
    # sample_files is a Path to a directory with test files
    result = process_single(str(sample_files), "http://tracker.com/announce")
    assert result == 0
    assert caplog.has_info("Success message")
```

### Test Configuration

The project uses `pytest.ini` for test configuration:

- Verbose test output
- Short traceback format
- Code coverage reporting (terminal and HTML)
- Detailed logging during tests
- Custom test markers

### Writing Tests

When writing new tests:

1. Use appropriate markers:
   ```python
   @pytest.mark.slow  # For time-consuming tests
   @pytest.mark.integration  # For integration tests
   ```

2. Use fixtures for common setup:
   ```python
   def test_file_processing(sample_files, clean_env):
       # Test implementation
   ```

3. Use logging assertions:
   ```python
   def test_with_logs(assert_logs):
       # Run code
       assert caplog.has_error("Expected error")
       assert "Message" in caplog.messages
   ```

4. Mock external dependencies:
   ```python
   @pytest.fixture
   def mock_dependency():
       with patch('module.Dependency') as mock:
           yield mock
   ```

### Coverage Reports

Test coverage reports are generated in two formats:
- Terminal output showing uncovered lines
- HTML report for detailed coverage analysis

To view the HTML coverage report:
```bash
# Run tests with coverage
pytest

# Open the report
open htmlcov/index.html
```

### Debugging Tests

For debugging failing tests:

```bash
# Show full traceback
pytest --tb=long

# Show logging output
pytest --log-cli-level=DEBUG

# Drop into debugger on failure
pytest --pdb

# Show local variables in traceback
pytest --showlocals
```


