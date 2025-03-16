"""Integration tests for edge cases and fuzzing."""

from __future__ import annotations

import os
import random
import string
import subprocess
import time
from pathlib import Path

import pytest

from torrent.utils.file_utils import sanitize_filename

def generate_random_string(length: int) -> str:
    """Generate a random string of given length."""
    # Use a more limited set of characters to avoid extreme edge cases
    chars = string.ascii_letters + string.digits + ' -_.'
    return ''.join(random.choice(chars) for _ in range(length))

def run_command(cmd: list[str]) -> tuple[str, str, int]:
    """Run a command and return its output."""
    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return process.stdout, process.stderr, process.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

@pytest.fixture
def large_file_dir(tmp_path: Path) -> Path:
    """Create a directory with a large file for testing."""
    test_dir = tmp_path / "large_sample"
    test_dir.mkdir()
    
    # Create a 10MB file with random data
    large_file = test_dir / "large_file.bin"
    with large_file.open("wb") as f:
        f.write(os.urandom(10 * 1024 * 1024))  # 10MB
        
    return test_dir

@pytest.fixture
def many_files_dir(tmp_path: Path) -> Path:
    """Create a directory with many small files."""
    test_dir = tmp_path / "many_files"
    test_dir.mkdir()
    
    # Create 1000 small files
    for i in range(1000):
        (test_dir / f"file_{i}.txt").write_text(f"content {i}")
        
    return test_dir

@pytest.fixture
def deep_nested_dir(tmp_path: Path) -> Path:
    """Create a deeply nested directory structure."""
    current_dir = tmp_path / "deep"
    current_dir.mkdir()
    
    # Create 10 levels of nesting
    for i in range(10):
        current_dir = current_dir / f"level_{i}"
        current_dir.mkdir()
        (current_dir / f"file_{i}.txt").write_text(f"content {i}")
        
    return tmp_path / "deep"

@pytest.fixture
def special_chars_dir(tmp_path: Path) -> Path:
    """Create a directory with special characters in names."""
    test_dir = tmp_path / "special_chars"
    test_dir.mkdir()
    
    # Create files with special characters
    special_names = [
        "file with spaces.txt",
        "file_with_unicode_🎉.txt",
        "file-with-dashes.txt",
        "file_with_@#$%.txt",
        "file_with_日本語.txt",
        ".hidden_file.txt"
    ]
    
    for name in special_names:
        (test_dir / name).write_text("test content")
        
    return test_dir

@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    """Create a sample directory with a few files for testing."""
    test_dir = tmp_path / "sample"
    test_dir.mkdir()
    
    # Create a few files of different sizes
    (test_dir / "small.txt").write_text("Small file content")
    with (test_dir / "medium.bin").open("wb") as f:
        f.write(os.urandom(1024 * 1024))  # 1MB
    (test_dir / "nested").mkdir()
    (test_dir / "nested" / "file.txt").write_text("Nested file content")
    
    return test_dir

@pytest.fixture
def multilingual_media_dir(tmp_path: Path) -> Path:
    """Create a directory structure with multilingual media names."""
    media_dir = tmp_path / "media_library"
    media_dir.mkdir()
    
    # Movies with special characters and different languages
    movies = [
        "Star Wars：新たなる希望 (1977) [1080p]",  # Japanese
        "기생충 Parasite 寄生虫 الطفيلي (2019) [4K]",  # Korean, Japanese, Arabic
        "Amélie - アメリ (2001) [720p]",  # French with Japanese
        "Вий 3D [Viy] Вій (2014) [BluRay]",  # Russian
        "El laberinto del fauno パンズ・ラビリンス (2006)",  # Spanish and Japanese
        "重慶森林 Chungking Express (1994)",  # Traditional Chinese
        "8½ - otto e mezzo [Criterion Collection]",  # Italian with special chars
        "2001: A Space Odyssey (70mm) [HDR]",  # Special characters
        "La Haine - الكراهية [1995]",  # French and Arabic
        "드라큘라 (Dracula) - 德古拉 [1992]"  # Korean and Chinese
    ]
    
    # Music albums with various scripts and special characters
    albums = [
        "Pink Floyd - The Dark Side of the Moon (1973) [24bit FLAC]",
        "坂本龍一 - Beauty (1989) [SACD]",  # Japanese
        "방탄소년단 - Map of the Soul: 7 [MP3 320]",  # Korean
        "محمد عبد الوهاب - Best of Collection [FLAC]",  # Arabic
        "Bjork - Homogenic [24-96 vinyl rip]",  # Simplified special chars
        "Владимир Высоцкий - Лучшее [MP3]",  # Russian
        "周杰倫 - 葉惠美 [FLAC]",  # Traditional Chinese
        "Mozart - Le Nozze di Figaro (1786) [DSD]",
        "שלמה ארצי - חצות [320kbps]",  # Hebrew
        "BABYMETAL - METAL RESISTANCE [Hi-Res]"  # Mixed scripts
    ]
    
    # Books with different languages and formats
    books = [
        "村上春樹 - 1Q84 [epub]",  # Japanese
        "Gabriel García Márquez - Cien años de soledad [PDF]",  # Spanish
        "Фёдор Достоевский - Преступление и наказание [mobi]",  # Russian
        "عبد الرحمن منيف - مدن الملح [PDF]",  # Arabic
        "米兰·昆德拉 - 生命中不能承受之轻 [epub]",  # Chinese
        "Paulo Coelho - O Alquimista [azw3]",  # Portuguese
        "한강 - 채식주의자 [epub]",  # Korean
        "Umberto Eco - Il nome della rosa [PDF]",  # Italian
        "אשכול נבו - שלוש קומות [mobi]",  # Hebrew
        "J.R.R. Tolkien - The Lord of the Rings [Illustrated Edition]"
    ]
    
    # Create directory structure and sample files
    categories = {
        "Movies": movies,
        "Music": albums,
        "Books": books
    }
    
    for category_name, items in categories.items():
        category_dir = media_dir / category_name
        category_dir.mkdir()
        
        for item in items:
            # Sanitize the item name for filesystem safety
            safe_item_name = sanitize_filename(item)
            item_dir = category_dir / safe_item_name
            item_dir.mkdir()
            # Create sample content file
            sample_file = item_dir / f"sample.{category_name.lower()}"
            with sample_file.open("wb") as f:
                f.write(os.urandom(1024 * 1024))  # 1MB sample file
            # Create .nfo file with UTF-8 description
            nfo_file = item_dir / "info.nfo"
            nfo_file.write_text(f"Title: {item}\nCategory: {category_name}\nSample file: {sample_file.name}", encoding="utf-8")
    
    return media_dir

def test_large_file_handling(large_file_dir: Path, tmp_path: Path) -> None:
    """Test handling of large files."""
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "-v",
        "--min-piece-size", "1M",  # Place before subcommand
        "--max-piece-size", "4M",  # Place before subcommand
        "file",
        str(large_file_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code == 0
    assert output.exists()
    assert "successfully" in (stdout or stderr).lower()

def test_many_files_handling(many_files_dir: Path, tmp_path: Path) -> None:
    """Test handling of directories with many files."""
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "-v",
        "file",
        str(many_files_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code == 0
    assert output.exists()
    assert "successfully" in (stdout or stderr).lower()

def test_deep_nesting_handling(deep_nested_dir: Path, tmp_path: Path) -> None:
    """Test handling of deeply nested directories."""
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "-v",
        "file",
        str(deep_nested_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code == 0
    assert output.exists()
    assert "successfully" in (stdout or stderr).lower()

def test_special_chars_handling(special_chars_dir: Path, tmp_path: Path) -> None:
    """Test handling of special characters in file names."""
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "-v",
        "file",
        str(special_chars_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code == 0
    assert output.exists()
    assert "successfully" in (stdout or stderr).lower()

def test_empty_directory(tmp_path: Path) -> None:
    """Test handling of empty directories."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    output = tmp_path / "output.torrent"
    
    cmd = [
        "torrent-directories",
        "-v",
        "file",
        str(empty_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code != 0  # Should fail for empty directories
    assert not output.exists()
    assert "error" in (stdout or stderr).lower()

def test_symlink_handling(tmp_path: Path) -> None:
    """Test handling of symbolic links."""
    # Create a directory with a file and a symlink
    test_dir = tmp_path / "symlink_test"
    test_dir.mkdir()
    (test_dir / "real_file.txt").write_text("real content")
    
    # Create a symlink to the file
    (test_dir / "link_file.txt").symlink_to(test_dir / "real_file.txt")
    
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "-v",
        "file",
        str(test_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code == 0
    assert output.exists()

@pytest.mark.parametrize("piece_size", [
    "16K",  # Minimum
    "256K",  # Default
    "1M",
    "16M",  # Maximum
    "15.5M",  # Non-power-of-2
    "17M",  # Above maximum
    "15K",  # Below minimum
    "invalid",  # Invalid format
])
def test_piece_size_handling(piece_size: str, sample_dir: Path, tmp_path: Path) -> None:
    """Test handling of various piece sizes."""
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "-v",
        "--min-piece-size", piece_size,  # Place before subcommand
        "file",
        str(sample_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    
    if piece_size in ["16K", "256K", "1M", "16M"]:
        assert code == 0
        assert output.exists()
        assert "successfully" in (stdout or stderr).lower()
    else:
        assert code != 0
        assert not output.exists()
        assert "error" in (stdout or stderr).lower()

def test_fuzzy_tracker_urls(sample_dir: Path, tmp_path: Path) -> None:
    """Test handling of various tracker URL formats."""
    output = tmp_path / "output.torrent"
    tracker_urls = [
        # Valid URLs - should be accepted
        ("http://tracker.example.com:6969/announce", True),   # Standard HTTP
        ("udp://tracker.example.com:6969/announce", True),    # UDP
        ("https://tracker.example.com/announce", True),       # HTTPS
        ("http://localhost/announce", True),                  # Local
        ("http://[2001:db8::1]:6969/announce", True),        # IPv6
        ("http://tracker.example.com", True),                 # No /announce path
        ("http://127.0.0.1:6969", True),                     # IP address
        
        # Invalid URLs - should be rejected
        ("ftp://tracker.example.com/announce", False),       # Unsupported protocol
        ("gopher://tracker.example.com", False),             # Unsupported protocol
        ("magnet:?xt=urn:btih:123", False),                 # Magnet link
        ("not_a_url", False),                               # Not a URL
        ("", False),                                        # Empty URL
        ("://invalid", False)                               # Missing protocol
    ]
    
    for url, should_succeed in tracker_urls:
        cmd = [
            "torrent-directories",
            "-v",
            "file",
            str(sample_dir),
            url,
            "-o",
            str(output)
        ]
        stdout, stderr, code = run_command(cmd)
        print(f"\nTesting tracker URL: {url}")
        print(f"stdout: {stdout}\nstderr: {stderr}\ncode: {code}")
        
        if should_succeed:
            assert code == 0, f"Expected success for URL: {url}"
            assert output.exists()
            assert "successfully" in (stdout or stderr).lower()
        else:
            assert code != 0, f"Expected failure for URL: {url}"
            assert "error" in (stdout or stderr).lower()
        
        # Clean up for next iteration
        if output.exists():
            output.unlink()

def test_fuzzy_input(tmp_path: Path) -> None:
    """Test handling of fuzzy/random input data."""
    test_dir = tmp_path / "fuzzy_test"
    test_dir.mkdir()
    
    # Create files with random names and content
    for _ in range(10):
        name_length = random.randint(1, 255)  # Max filename length
        content_length = random.randint(0, 1024)  # Random content length
        
        filename = generate_random_string(name_length)
        content = generate_random_string(content_length)
        
        try:
            (test_dir / filename).write_text(content)
        except OSError:
            # Skip if filename is invalid for the filesystem
            continue
    
    output = tmp_path / "output.torrent"
    cmd = [
        "torrent-directories",
        "-v",
        "file",
        str(test_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    stdout, stderr, code = run_command(cmd)
    print(f"\nCommand output:\nstdout: {stdout}\nstderr: {stderr}\ncode: {code}")
    assert code == 0
    assert output.exists()
    assert "successfully" in (stdout or stderr).lower()

def test_multilingual_media_torrents(multilingual_media_dir: Path, tmp_path: Path) -> None:
    """Test creating torrents from directories with multilingual names."""
    output_dir = tmp_path / "torrents"
    output_dir.mkdir()
    
    # Test each media category separately
    categories = ["Movies", "Music", "Books"]
    for category in categories:
        category_dir = multilingual_media_dir / category
        category_output = output_dir / category
        category_output.mkdir()
        
        cmd = [
            "torrent-directories",
            "-v",
            "batch",
            str(category_dir),
            "http://tracker.example.com:6969/announce",
            "-o",
            str(category_output)
        ]
        
        start_time = time.time()
        stdout, stderr, code = run_command(cmd)
        processing_time = time.time() - start_time
        
        # Verify results
        assert code == 0, f"Failed to process {category} with stdout:\n{stdout}\nstderr:\n{stderr}"
        assert category_output.exists()
        
        # Check that all torrents were created
        torrent_files = list(category_output.glob("*.torrent"))
        expected_count = 10  # We created 10 items in each category
        assert len(torrent_files) == expected_count, f"Expected {expected_count} torrent files for {category}, got {len(torrent_files)}"
        
        # Verify torrent file names are valid UTF-8
        for torrent_file in torrent_files:
            try:
                # Try to read the filename as UTF-8
                torrent_file.name.encode('utf-8').decode('utf-8')
            except UnicodeEncodeError:
                pytest.fail(f"Torrent filename is not valid UTF-8: {torrent_file.name}")
        
        print(f"\nProcessed {category} in {processing_time:.2f} seconds")
        # Each category should process quickly since files are small
        assert processing_time < 30, f"{category} processing took too long: {processing_time:.2f} seconds" 