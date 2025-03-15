"""
Configuration handling for command-line arguments.
"""
from __future__ import annotations

import argparse
from typing import Optional

from ..utils.config import TorrentConfig

def parse_size(size_str: str) -> int:
    """
    Parse a human readable size string into bytes.
    
    Args:
        size_str: Size string (e.g. '256K', '16M')
        
    Returns:
        Size in bytes
        
    Raises:
        ValueError: If the format is invalid
    """
    if not size_str:
        raise ValueError("Size string cannot be empty")
        
    units = {
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024
    }
    
    size_str = size_str.upper()
    if size_str[-1] in units:
        number = float(size_str[:-1])
        return int(number * units[size_str[-1]])
    return int(size_str)

def create_torrent_config(args: argparse.Namespace) -> TorrentConfig:
    """
    Create a TorrentConfig from command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Configured TorrentConfig instance
        
    Raises:
        ValueError: If argument values are invalid
    """
    config = TorrentConfig()
    
    if args.min_piece_size:
        config.min_piece_size = parse_size(args.min_piece_size)
    if args.max_piece_size:
        config.max_piece_size = parse_size(args.max_piece_size)
        
    if args.target_pieces:
        try:
            min_pieces, max_pieces = map(int, args.target_pieces.split('-'))
            config.target_pieces_min = min_pieces
            config.target_pieces_max = max_pieces
        except ValueError:
            raise ValueError("Invalid target pieces format. Use MIN-MAX (e.g. 1000-2000)")
            
    if args.include_hidden:
        config.skip_hidden = False
    if args.include_system:
        config.skip_system_files = False
        
    return config 