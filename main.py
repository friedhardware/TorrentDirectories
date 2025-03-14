#!/usr/bin/env python3
import sys
from torrent_utils import create_torrent, create_directory_torrents

def print_usage():
    print("""Usage:
    Single file/directory:
        main.py file [path to file or directory] [tracker-url]
    
    Batch directory processing:
        main.py batch [parent directory] [tracker-url]""")

def main():
    if len(sys.argv) < 4:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    path = sys.argv[2]
    tracker_url = sys.argv[3]
    
    try:
        if command == "file":
            torrent_path = create_torrent(path, tracker_url)
            print(f"\nTorrent created: {torrent_path}")
        
        elif command == "batch":
            create_directory_torrents(path, tracker_url)
        
        else:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
