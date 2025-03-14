import math

def calculate_optimal_piece_size(total_size):
    """
    Calculate the optimal piece size for a torrent based on its total size.
    
    Guidelines:
    - Minimum piece size: 256 KiB
    - Maximum piece size: 16 MiB
    - Target number of pieces: Between 1000 and 2000 for optimal balance
    - Piece size must be a power of 2
    
    Args:
        total_size (int): Total size of the torrent in bytes
    
    Returns:
        int: Optimal piece size in bytes
    """
    MIN_PIECE_SIZE = 256 * 1024  # 256 KiB
    MAX_PIECE_SIZE = 16 * 1024 * 1024  # 16 MiB
    TARGET_PIECES_MAX = 2000
    
    # Start with minimum piece size that would result in <= 2000 pieces
    min_viable_piece_size = math.ceil(total_size / TARGET_PIECES_MAX)
    
    # Round up to nearest power of 2
    min_viable_power = math.ceil(math.log2(min_viable_piece_size))
    piece_size = 2 ** min_viable_power
    
    # Ensure piece size is within bounds
    piece_size = max(MIN_PIECE_SIZE, min(piece_size, MAX_PIECE_SIZE))
    
    return piece_size 