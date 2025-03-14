# Torrent Directories

A Python tool for creating torrent files from directories or single files with optimal piece size calculation.

## Features

- Create torrents from single files or entire directories
- Automatically calculate optimal piece size based on total content size
- Skip hidden files and system files (like Thumbs.db)
- Configurable piece size bounds (256 KiB - 16 MiB)

## Requirements

- Python 3.x
- libtorrent

## Usage

```bash
python main.py [path to file or directory] [tracker-url]
```

Example:
```bash
python main.py /path/to/content http://tracker.example.com/announce
```

## Testing

Run the test suite:
```bash
python -m unittest test_torrent_utils.py -v
``` 