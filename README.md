# Torrent Directories

A Python tool for creating torrent files from directories or single files with optimal piece size calculation.

## Features

- Create torrents from single files or entire directories
- Automatically calculate optimal piece size based on total content size
- Skip hidden files and system files (like Thumbs.db)
- Configurable piece size bounds (256 KiB - 16 MiB)
- Batch creation of torrents from subdirectories
- Resume support for batch processing using manifest tracking

## Prerequisite

Install the Python libtorrent bindings using the installation script from [python-libtorrent-binding](https://github.com/userdocs/python-libtorrent-binding):

```bash
curl -sLO https://raw.githubusercontent.com/userdocs/python-libtorrent-binding/refs/heads/master/libtorrent-python.bash
chmod +x libtorrent-python.bash
./libtorrent-python.bash
```

Using sudo or root, install the dependencies using `sudo ./libtorrent-python.bash install`. After the dependencies are setup, exit root and then procede to install the libtorrent-python-bindings.

`./libtorrent-python.bash all`

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
5. Maintain a manifest file to track processed directories

The manifest tracking allows you to safely interrupt and resume batch processing. When you run the batch command again:
- Previously processed directories will be skipped
- Only new directories will be processed
- The manifest file (`manifest.csv`) is automatically maintained in the output directory

### Manifest File

The tool uses a CSV manifest file (`manifest.csv`) to track which directories have been processed. The manifest contains:
- Full path to the source directory
- Name of the created torrent file
- Timestamp when the torrent was created (in ISO 8601 format)

Example manifest.csv:
```csv
"directory_path","torrent_file","processed_at"
"/path/to/movies/The Matrix (1999)","The Matrix (1999).torrent","2024-03-14T15:30:45"
"/path/to/movies/Alien (1979)","Alien (1979).torrent","2024-03-14T15:31:12"
```

The manifest is append-only for better resilience against interruptions. Each entry is written immediately after its torrent is created.

### Manifest Validation

The tool performs thorough validation of the manifest state against the actual files:

1. **Fresh Start (Valid)**
   - No manifest file and no torrent files exist
   - This is considered a valid first run

2. **Perfect Match (Valid)**
   - All torrent files listed in manifest exist on disk
   - All torrent files on disk are listed in manifest
   - Processing continues normally, skipping previously processed directories

3. **Discrepancies Found (Warning)**
   The tool will detect and report:
   - Torrent files listed in manifest but missing from disk
   - Torrent files found but not listed in manifest
   
   For each discrepancy, it shows:
   - The torrent filename
   - The source directory path (for missing files)
   - When it was processed (for missing files)
   
   You will be prompted to:
   - Proceed and rebuild missing torrents/update manifest (type 'y')
   - Cancel without making changes (type 'N', default)

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
  ├── manifest.csv
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


