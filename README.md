# TorrentDirectories

A Python tool for creating torrent files from directories with optimal settings and batch processing capabilities.

## Features

- Create torrents from single files or directories
- Batch process multiple directories with resume support
- Optimal piece size calculation:
  - Smaller pieces (256 KiB) for better granular downloading
  - Larger pieces (16 MiB) for reduced overhead
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

### Basic Commands

1. Create a torrent from a single file or directory:
```bash
torrent-directories file path/to/content http://tracker.example.com:6969/announce
```

2. Process all subdirectories in a parent directory:
```bash
torrent-directories batch path/to/parent http://tracker.example.com:6969/announce
```

### Common Options

Global options that work with all commands:
```bash
# Show version
torrent-directories --version

# Enable verbose output
torrent-directories -v [command] [args]

# Write logs to file
torrent-directories --log-file path/to/log.txt [command] [args]

# Preview changes without making them
torrent-directories --dry-run [command] [args]
```

### Torrent Creation Options

Configure how torrents are created:
```bash
# Custom piece sizes
torrent-directories file --min-piece-size 512K --max-piece-size 32M path/to/content tracker-url

# Custom target piece count
torrent-directories file --target-pieces 1000-2000 path/to/content tracker-url

# Include hidden/system files
torrent-directories file --include-hidden --include-system path/to/content tracker-url
```

### Single File/Directory Mode

Options specific to the `file` command:
```bash
# Custom output path
torrent-directories file -o output.torrent path/to/content tracker-url

# Force overwrite existing torrent
torrent-directories file --force path/to/content tracker-url
```

### Batch Processing Mode

Options specific to the `batch` command:
```bash
# Clean manifest of missing entries
torrent-directories batch --clean path/to/parent tracker-url

# Use custom manifest file
torrent-directories batch --manifest custom_manifest.csv path/to/parent tracker-url

# Force rebuild of existing torrents
torrent-directories batch --force path/to/parent tracker-url

# Stop after 3 failures
torrent-directories batch --max-failures 3 path/to/parent tracker-url
```

### Example Workflows

1. Create a torrent with detailed logging:
```bash
torrent-directories -v --log-file create.log file \
    --min-piece-size 1M \
    --max-piece-size 16M \
    path/to/movie \
    http://tracker.example.com:6969/announce
```

2. Preview batch processing with custom settings:
```bash
torrent-directories --dry-run batch \
    --include-hidden \
    --target-pieces 1500-3000 \
    --manifest custom.csv \
    /path/to/movies \
    http://tracker.example.com:6969/announce
```

3. Process a directory with error handling:
```bash
torrent-directories -v batch \
    --clean \
    --max-failures 5 \
    --force \
    /path/to/movies \
    http://tracker.example.com:6969/announce
```

## Manifest System

The tool maintains a CSV manifest file (`manifest.csv`) to track processed directories:

```csv
directory_path,torrent_file,processed_at
/path/to/movie1,movie1.torrent,2024-03-15T14:30:00
/path/to/movie2,movie2.torrent,2024-03-15T14:35:00
```

### Safety Features

- Append-only writes for data integrity
- Immediate entry recording after successful torrent creation
- Header validation on file load
- Backup creation before modifications
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

creator = TorrentCreator(tracker_url, config)
torrent_path = creator.create_torrent(input_path, output_path=None)
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


