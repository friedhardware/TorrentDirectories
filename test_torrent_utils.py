import unittest
from torrent_utils import calculate_optimal_piece_size

class TestTorrentUtils(unittest.TestCase):
    def test_small_file(self):
        # Test with 100 KiB file (smaller than min piece size)
        size = 100 * 1024  # 100 KiB
        piece_size = calculate_optimal_piece_size(size)
        self.assertEqual(piece_size, 256 * 1024)  # Should use minimum piece size
        
    def test_medium_file(self):
        # Test with 1 GiB file
        size = 1024 * 1024 * 1024  # 1 GiB
        piece_size = calculate_optimal_piece_size(size)
        # Should be between min and max, and a power of 2
        self.assertTrue(256 * 1024 <= piece_size <= 16 * 1024 * 1024)
        self.assertEqual(piece_size & (piece_size - 1), 0)  # Check if power of 2
        
    def test_large_file(self):
        # Test with 100 GiB file
        size = 100 * 1024 * 1024 * 1024  # 100 GiB
        piece_size = calculate_optimal_piece_size(size)
        # Should use maximum piece size
        self.assertEqual(piece_size, 16 * 1024 * 1024)
        
    def test_piece_count_bounds(self):
        # Test that number of pieces stays within target range for various sizes
        test_sizes = [
            50 * 1024 * 1024,      # 50 MiB
            500 * 1024 * 1024,     # 500 MiB
            5 * 1024 * 1024 * 1024 # 5 GiB
        ]
        
        for size in test_sizes:
            piece_size = calculate_optimal_piece_size(size)
            num_pieces = size / piece_size
            self.assertLessEqual(num_pieces, 2000, 
                f"Too many pieces ({num_pieces}) for size {size}")
            
    def test_power_of_two(self):
        # Test that piece sizes are always powers of 2
        test_sizes = [
            1024 * 1024,       # 1 MiB
            10 * 1024 * 1024,  # 10 MiB
            100 * 1024 * 1024  # 100 MiB
        ]
        
        for size in test_sizes:
            piece_size = calculate_optimal_piece_size(size)
            # Check if number is power of 2 using bitwise operation
            self.assertEqual(piece_size & (piece_size - 1), 0,
                f"Piece size {piece_size} is not a power of 2")

if __name__ == '__main__':
    unittest.main() 