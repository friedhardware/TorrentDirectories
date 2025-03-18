Best Practices & Advanced Usage
============================

This guide covers best practices and advanced usage patterns for TorrentDirectories, based on real-world experience and testing.

Directory Organization
--------------------

When organizing your content for torrent creation, follow these guidelines:

1. **Consistent Structure**: Keep a consistent directory structure, especially for batch processing:

   .. code-block:: text

       media/
       ├── Movies/
       │   ├── Movie1 (2024)/
       │   │   ├── movie.mkv
       │   │   └── extras/
       │   └── Movie2 (2024)/
       │       └── movie.mkv
       ├── TV/
       │   └── Show Name/
       │       ├── Season 01/
       │       └── Season 02/
       └── Music/
           └── Artist/
               └── Album (Year)/

2. **File Naming**: Use clear, consistent file naming:
   - Avoid special characters that might cause issues
   - Include relevant metadata in folder names (year, quality, etc.)
   - Use appropriate file extensions

3. **Clean Content**:
   - Remove unnecessary files (`.DS_Store`, `Thumbs.db`, etc.)
   - Delete partial downloads or temporary files
   - Consider using ``--skip-empty-files`` for robustness

Optimizing Piece Sizes
--------------------

The tool automatically calculates optimal piece sizes, but you can fine-tune for specific scenarios:

1. **Large 4K Movies** (50GB+):

   .. code-block:: bash

       torrent-directories file "Movie (2024)/movie.mkv" \
           http://tracker.example.com/announce \
           --min-piece-size 4M \
           --max-piece-size 32M

   This reduces the number of pieces while maintaining reasonable chunk sizes for verification.

2. **Small Files** (under 100MB):

   .. code-block:: bash

       torrent-directories file "Small Content/" \
           http://tracker.example.com/announce \
           --min-piece-size 32K \
           --max-piece-size 256K

   Smaller piece sizes help with partial downloading and reduce wasted bandwidth.

3. **Mixed Content** (TV seasons with varying episode sizes):

   .. code-block:: bash

       torrent-directories file "TV Show/Season 01/" \
           http://tracker.example.com/announce \
           --min-piece-size 512K \
           --max-piece-size 4M

   This provides a good balance for mixed file sizes.

Batch Processing Strategies
------------------------

1. **Incremental Updates**:

   When regularly adding new content:

   .. code-block:: bash

       # First run - process everything
       torrent-directories batch ./media http://tracker.example.com/announce \
           -o ./torrents \
           --skip-empty-files

       # Later runs - only process new content
       torrent-directories batch ./media http://tracker.example.com/announce \
           -o ./torrents \
           --skip-empty-files

   The manifest system tracks what's been processed, so only new content is handled.

2. **Parallel Processing**:

   For large collections, process different types simultaneously:

   .. code-block:: bash

       # In terminal 1 - Process movies
       torrent-directories batch ./media/Movies \
           http://tracker.example.com/announce \
           -o ./torrents/movies

       # In terminal 2 - Process TV shows
       torrent-directories batch ./media/TV \
           http://tracker.example.com/announce \
           -o ./torrents/tv

3. **Staged Processing**:

   For very large collections:

   .. code-block:: bash

       # Stage 1: Process with higher failure tolerance
       torrent-directories batch ./media \
           http://tracker.example.com/announce \
           -o ./torrents \
           --skip-empty-files \
           --max-failures 100

       # Stage 2: Clean up the manifest
       torrent-directories batch ./media \
           http://tracker.example.com/announce \
           -o ./torrents \
           --clean

       # Stage 3: Retry with stricter settings
       torrent-directories batch ./media \
           http://tracker.example.com/announce \
           -o ./torrents \
           --max-failures 0

Metadata Best Practices
--------------------

1. **Consistent Source Tags**:

   .. code-block:: bash

       torrent-directories batch ./media http://tracker.example.com/announce \
           --source "MyGroup" \
           --comment "Release Info: {directory_name}"

2. **Informative Comments**:

   Include relevant information in comments:

   - Release specifications
   - Encoding details
   - Source information
   - Special notes

   .. code-block:: bash

       torrent-directories file "Movie (2024)/movie.mkv" \
           http://tracker.example.com/announce \
           --comment "2160p HDR | Source: REMUX | Audio: TrueHD 7.1"

3. **Private Flag Usage**:

   - Use ``--private`` (default) for private tracker releases
   - Use ``--public`` for public trackers or DHT/PEX enabled releases

Error Handling and Recovery
------------------------

1. **Graceful Failure Handling**:

   .. code-block:: bash

       torrent-directories batch ./media http://tracker.example.com/announce \
           --skip-empty-files \
           --max-failures 5 \
           --log-file errors.log

2. **Recovery Process**:

   If batch processing fails:

   .. code-block:: bash

       # 1. Clean the manifest
       torrent-directories batch ./media \
           http://tracker.example.com/announce \
           --clean

       # 2. Force reprocess problem directories
       torrent-directories batch ./media \
           http://tracker.example.com/announce \
           --force

3. **Verification**:

   Always verify created torrents:

   .. code-block:: bash

       # Use dry-run first
       torrent-directories --dry-run batch ./media \
           http://tracker.example.com/announce

       # Then process with verbose output
       torrent-directories -v batch ./media \
           http://tracker.example.com/announce

Automation Tips
-------------

1. **Shell Scripts**:

   Create wrapper scripts for common operations:

   .. code-block:: bash

       #!/bin/bash

       # process_new_content.sh
       MEDIA_DIR="./media"
       TORRENTS_DIR="./torrents"
       TRACKER="http://tracker.example.com/announce"

       # Process new content
       torrent-directories batch "$MEDIA_DIR" "$TRACKER" \
           -o "$TORRENTS_DIR" \
           --skip-empty-files \
           --source "MyGroup" \
           --comment "Auto-processed: $(date)"

2. **Cron Jobs**:

   Schedule regular processing:

   .. code-block:: bash

       # Add to crontab:
       0 4 * * * /path/to/process_new_content.sh >> /var/log/torrent-processing.log 2>&1

3. **Integration Scripts**:

   Example script to process and upload:

   .. code-block:: python

       from pathlib import Path
       from torrent.torrent_creator import TorrentCreator
       from torrent.utils.config import TorrentConfig

       def process_and_upload(media_dir, tracker_url):
           config = TorrentConfig(
               tracker_url=tracker_url,
               private=True,
               skip_empty_files=True
           )

           creator = TorrentCreator(config)

           for item in Path(media_dir).iterdir():
               if item.is_dir():
                   torrent_path = f"torrents/{item.name}.torrent"
                   creator.create(str(item), torrent_path)
                   # Add your upload logic here
                   upload_torrent(torrent_path)

Performance Optimization
---------------------

1. **Memory Usage**:
   - Process larger directories in segments
   - Use appropriate piece sizes for content type
   - Monitor system resources during batch operations

2. **Disk I/O**:
   - Place output torrents on a different disk than source content
   - Consider using SSD for manifest and temporary files
   - Avoid processing while content is being written

3. **Network Considerations**:
   - Use local tracker URLs during testing
   - Consider bandwidth when verifying large torrents
   - Use appropriate piece sizes for network conditions

Security Considerations
--------------------

1. **Private Torrents**:
   - Always use ``--private`` for private tracker releases
   - Verify tracker URLs are correct
   - Don't include sensitive information in metadata

2. **File Permissions**:
   - Ensure appropriate read permissions on source content
   - Set appropriate write permissions for output directories
   - Protect manifest files from unauthorized access

3. **API Keys and Credentials**:
   - Never include API keys in torrent metadata
   - Use environment variables for sensitive information
   - Regularly rotate credentials used in automation
