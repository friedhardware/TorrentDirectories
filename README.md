# Torrent Directories

A Python tool for creating torrent files from directories or single files with optimal piece size calculation.

## Features

- Create torrents from single files or entire directories
- Automatically calculate optimal piece size based on total content size
- Skip hidden files and system files (like Thumbs.db)
- Configurable piece size bounds (256 KiB - 16 MiB)
- Batch creation of torrents from subdirectories

## Requirements

- Python 3.x
- libtorrent

## Usage

The script supports two modes of operation:

### Single File/Directory Mode

Create a torrent for a single file or directory:
```bash
python main.py file [path to file or directory] [tracker-url]
```

Example:
```bash
python main.py file "/path/to/content" "http://tracker.example.com/announce"
```

### Batch Directory Mode

Process all subdirectories in a parent directory, creating a separate torrent for each:
```bash
python main.py batch [parent directory] [tracker-url]
```

Example:
```bash
python main.py batch /movies "http://tracker.example.com/announce"
```

This will:
1. Scan the parent directory for subdirectories
2. Create an output directory named "[parent_dir]_torrents" (e.g., "movies_torrents")
3. Generate a separate .torrent file for each subdirectory
4. Name each .torrent file after its corresponding subdirectory

For example, if your movies directory contains:
```
/movies/
  ├── Hanna (2009)/
  ├── Alien (1979)/
  └── The Matrix (1999)/
```

It will create:
```
/movies_torrents/
  ├── Hanna (2009).torrent
  ├── Alien (1979).torrent
  └── The Matrix (1999).torrent
```

## Testing

Run the test suite:
```bash
python -m unittest test_torrent_utils.py -v
```

## API

The `torrent_utils` module provides the following functions:

### `create_torrent(input_path: str, tracker_url: str, output_path: Optional[str] = None) -> str`

Create a torrent file from a single file or directory.

### `create_directory_torrents(parent_dir: str, tracker_url: str, output_dir: Optional[str] = None) -> list[str]`

Create torrent files for each subdirectory in the specified directory. If `output_dir` is not provided, it will create a directory named "[parent_dir]_torrents". 