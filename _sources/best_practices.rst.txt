Best Practices Guide
==================

This guide provides best practices for using TorrentDirectories effectively.

Directory Organization
--------------------

Structure Your Content
~~~~~~~~~~~~~~~~~~~~

Organize your content in a way that makes sense for batch processing:

- Keep related content in separate directories
- Use consistent naming conventions
- Avoid deeply nested directories
- Keep file and directory names simple and descriptive

Example structure::

    parent_directory/
    ├── movie1/
    │   ├── movie1.mkv
    │   └── subtitles/
    ├── movie2/
    │   ├── movie2.mkv
    │   └── extras/
    └── movie3/
        └── movie3.mkv

Piece Size Optimization
---------------------

Understanding Piece Sizes
~~~~~~~~~~~~~~~~~~~~~~~

Piece size affects both torrent creation and download performance:

- Smaller pieces (16 KiB - 1 MiB):
  - Better for small files
  - More precise resume capability
  - Larger .torrent files
  - More CPU usage during verification

- Larger pieces (1 MiB - 16 MiB):
  - Better for large files
  - Smaller .torrent files
  - Less CPU usage during verification
  - Less precise resume capability

Recommended Settings
~~~~~~~~~~~~~~~~~~

Based on content type:

- Small files (< 100 MB):
  ``--min-piece-size 16K --max-piece-size 1M``

- Medium files (100 MB - 1 GB):
  ``--min-piece-size 256K --max-piece-size 4M``

- Large files (1 GB - 10 GB):
  ``--min-piece-size 1M --max-piece-size 16M``

- Very large files (> 10 GB):
  ``--min-piece-size 4M --max-piece-size 32M``

Batch Processing Strategies
-------------------------

Efficient Processing
~~~~~~~~~~~~~~~~~~

When processing multiple directories:

1. Start with a dry run::

    torrent-directories --dry-run batch ./content http://tracker.example.com/announce

2. Use the manifest system effectively:
   - Clean periodically with ``--clean``
   - Use ``--force`` only when needed
   - Set appropriate ``--max-failures``

3. Monitor progress with verbose output::

    torrent-directories -v batch ./content http://tracker.example.com/announce

4. Use output directory organization::

    torrent-directories batch ./content http://tracker.example.com/announce \
        -o ./torrents/%Y/%m/%d

Resume and Recovery
~~~~~~~~~~~~~~~~~

Handle interruptions gracefully:

1. The manifest tracks progress automatically
2. Use ``--clean`` to remove invalid entries
3. Set ``--max-failures`` based on your needs
4. Check logs for detailed error information

Metadata Best Practices
---------------------

Consistent Information
~~~~~~~~~~~~~~~~~~~~

Maintain consistent metadata across your torrents:

1. Use a standard source tag::

    torrent-directories file ./content http://tracker.example.com/announce \
        --source "MyReleaseGroup"

2. Add helpful comments::

    torrent-directories file ./content http://tracker.example.com/announce \
        --comment "Release details: ..."

3. Consider privacy settings carefully::

    # Private tracker
    torrent-directories file ./content http://tracker.example.com/announce --private

    # Public tracker
    torrent-directories file ./content http://tracker.example.com/announce --public

Error Handling
-------------

Preventive Measures
~~~~~~~~~~~~~~~~~

1. Check permissions before starting
2. Verify content integrity
3. Use ``--skip-empty-files`` when appropriate
4. Set reasonable ``--max-failures`` limits

Recovery Steps
~~~~~~~~~~~~

When errors occur:

1. Check logs for detailed information
2. Use ``--clean`` to fix manifest issues
3. Verify output directory permissions
4. Check for conflicting files

Automation Tips
-------------

Scripting Integration
~~~~~~~~~~~~~~~~~~~

When integrating with scripts:

1. Use exit codes for flow control::

    if torrent-directories file ./content http://tracker.example.com/announce; then
        echo "Success"
    else
        echo "Failed"
    fi

2. Parse JSON output in verbose mode
3. Use log files for record keeping
4. Implement proper error handling

Scheduled Tasks
~~~~~~~~~~~~~

For automated processing:

1. Use absolute paths
2. Set up proper logging
3. Handle errors appropriately
4. Monitor disk space

Performance Optimization
----------------------

System Resources
~~~~~~~~~~~~~~

Optimize resource usage:

1. Set appropriate piece sizes
2. Use manifest caching
3. Monitor memory usage
4. Consider disk I/O

Concurrent Processing
~~~~~~~~~~~~~~~~~~~

When running multiple instances:

1. Use separate output directories
2. Monitor system resources
3. Set appropriate timeouts
4. Handle lock files properly

Security Considerations
---------------------

File System Safety
~~~~~~~~~~~~~~~~

Protect your data:

1. Use appropriate permissions
2. Create backups before operations
3. Verify file integrity
4. Handle special files safely

Network Security
~~~~~~~~~~~~~~

When using trackers:

1. Verify tracker URLs
2. Use HTTPS when available
3. Handle redirects carefully
4. Validate tracker responses

Testing Guidelines
----------------

Test Coverage
~~~~~~~~~~~

Maintain comprehensive tests:

1. Test both success and failure paths
2. Include edge cases
3. Verify error handling
4. Test progress reporting
5. Validate torrent metadata
6. Test with various file types

Test Organization
~~~~~~~~~~~~~~

Structure tests effectively:

1. Use fixtures for common setup
2. Test at multiple levels:
   - Unit tests
   - Integration tests
   - CLI tests
   - End-to-end tests
3. Include performance tests
4. Test concurrent operations

Maintenance
----------

Regular Tasks
~~~~~~~~~~~

Keep your system healthy:

1. Clean manifests regularly
2. Archive old torrent files
3. Monitor disk space
4. Update configurations

Troubleshooting
~~~~~~~~~~~~~

When issues arise:

1. Check logs first
2. Verify file permissions
3. Test in isolation
4. Use verbose output
