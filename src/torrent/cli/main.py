"""
Main entry point for the command-line interface.
"""
from __future__ import annotations

import logging
import sys
from typing import List, Optional

from .parser import create_parser
from .config import create_torrent_config
from .commands import process_single, process_batch

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """
    Configure logging with appropriate level and format.
    
    Args:
        verbose: Whether to show debug level messages
        log_file: Optional path to write logs to
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    format_str = '%(asctime)s - %(levelname)s - %(message)s' if verbose else '%(message)s'
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(format_str))
    root_logger.addHandler(console)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(file_handler)

def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the command-line interface.
    
    Args:
        args: Command line arguments (uses sys.argv if None)
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args(args)
    
    try:
        # Setup logging first
        setup_logging(args.verbose, args.log_file)
        
        # Create torrent configuration from arguments
        config = create_torrent_config(args)
        
        if args.command == 'file':
            return process_single(args.path, args.tracker, args.output,
                               config=config, dry_run=args.dry_run,
                               force=args.force)
        elif args.command == 'batch':
            return process_batch(args.directory, args.tracker,
                               clean=args.clean, config=config,
                               output_dir=args.output,
                               dry_run=args.dry_run,
                               force=args.force,
                               max_failures=args.max_failures)
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            logger.exception("Detailed error information:")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 