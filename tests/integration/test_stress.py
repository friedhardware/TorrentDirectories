"""Integration tests for stress testing and performance."""

import subprocess
from pathlib import Path
import pytest
import time
import os
import shutil
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor

def run_command(cmd: list[str]) -> tuple[str, str, int]:
    """Run a command and return stdout, stderr, and return code."""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode

def create_large_file(file_info: tuple[Path, int]) -> tuple[str, float]:
    """Create a single large file.
    
    Args:
        file_info: Tuple of (file_path, file_number)
        
    Returns:
        Tuple of (filename, size_in_gb)
    """
    file_path, file_num = file_info
    
    with file_path.open("wb") as f:
        chunk_size = 64 * 1024 * 1024  # 64MB chunks
        remaining = 1 * 1024 * 1024 * 1024  # 1GB
        chunks_written = 0
        while remaining > 0:
            write_size = min(chunk_size, remaining)
            f.write(os.urandom(write_size))
            remaining -= write_size
            chunks_written += 1
    
    size_gb = file_path.stat().st_size / (1024 * 1024 * 1024)
    return file_path.name, size_gb

@pytest.fixture
def huge_files_dir(tmp_path: Path) -> Path:
    """Create a directory with multiple large files for stress testing."""
    test_dir = tmp_path / "huge_files"
    test_dir.mkdir()
    
    # Prepare file paths and numbers
    file_infos = [
        (test_dir / f"large_file_{i}.bin", i)
        for i in range(5)
    ]
    
    start_time = time.time()
    
    # Create files in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(create_large_file, file_infos))
    
    # Calculate and display total size
    total_size = sum(size for _, size in results)
    duration = time.time() - start_time
    
    return test_dir

@pytest.fixture
def many_small_files_dir(tmp_path: Path) -> Path:
    """Create a directory with many tiny files."""
    test_dir = tmp_path / "many_small"
    test_dir.mkdir()
    
    # Create 10,000 tiny files
    for i in range(10000):
        (test_dir / f"file_{i}.txt").write_text(f"content {i}")
        
    return test_dir

@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    """Create a sample directory with a few files for concurrent testing."""
    test_dir = tmp_path / "sample"
    test_dir.mkdir()
    
    # Create a few files of different sizes
    (test_dir / "small.txt").write_text("Small file content")
    with (test_dir / "medium.bin").open("wb") as f:
        f.write(os.urandom(1024 * 1024))  # 1MB
    (test_dir / "nested").mkdir()
    (test_dir / "nested" / "file.txt").write_text("Nested file content")
    
    return test_dir

def get_process_memory() -> float:
    """Get the current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)  # Convert to MB

def test_large_files_memory_usage(huge_files_dir: Path, tmp_path: Path) -> None:
    """Test memory usage when processing large files."""
    output = tmp_path / "output.torrent"
    
    # Measure initial memory
    initial_memory = get_process_memory()
    
    cmd = [
        "torrent-directories",
        "-v",
        "--min-piece-size", "16M",  # Increased piece size for larger files
        "--max-piece-size", "64M",  # Increased piece size for larger files
        "file",
        str(huge_files_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    
    start_time = time.time()
    stdout, stderr, code = run_command(cmd)
    duration = time.time() - start_time
    peak_memory = get_process_memory()
    
    assert code == 0
    assert output.exists()
    # Memory usage should be reasonable (less than 60MB since we're using efficient streaming)
    assert peak_memory - initial_memory < 60  # Less than 60MB increase
    # Processing should complete within 5 minutes for 5GB of data
    assert duration < 300  # 5 minutes max

def test_many_files_performance(many_small_files_dir: Path, tmp_path: Path) -> None:
    """Test performance with many small files."""
    output = tmp_path / "output.torrent"
    
    start_time = time.time()
    cmd = [
        "torrent-directories",
        "-v",
        "file",
        str(many_small_files_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output)
    ]
    stdout, stderr, code = run_command(cmd)
    end_time = time.time()
    
    processing_time = end_time - start_time
    print(f"\nProcessing time: {processing_time:.2f} seconds")
    
    assert code == 0
    assert output.exists()
    # Based on previous results, this should complete much faster
    assert processing_time < 30  # Should complete within 30 seconds

def test_concurrent_processing(sample_dir: Path, tmp_path: Path) -> None:
    """Test running multiple torrent creations concurrently."""
    num_concurrent = 5
    outputs = [tmp_path / f"output_{i}.torrent" for i in range(num_concurrent)]
    
    def create_torrent(output: Path) -> tuple[float, int]:
        start_time = time.time()
        cmd = [
            "torrent-directories",
            "-v",
            "file",
            str(sample_dir),
            "http://tracker.example.com:6969/announce",
            "-o",
            str(output)
        ]
        _, _, code = run_command(cmd)
        end_time = time.time()
        return end_time - start_time, code
    
    with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        results = list(executor.map(create_torrent, outputs))
    
    # Check results
    processing_times = [r[0] for r in results]
    exit_codes = [r[1] for r in results]
    
    print(f"\nConcurrent processing times: {[f'{t:.2f}s' for t in processing_times]}")
    print(f"Exit codes: {exit_codes}")
    
    assert all(code == 0 for code in exit_codes)
    assert all(output.exists() for output in outputs)

def test_interrupted_processing(huge_files_dir: Path, tmp_path: Path) -> None:
    """Test handling of interrupted processing."""
    output = tmp_path / "output.torrent"
    
    def run_in_thread():
        cmd = [
            "torrent-directories",
            "-v",
            "file",
            str(huge_files_dir),
            "http://tracker.example.com:6969/announce",
            "-o",
            str(output)
        ]
        process = subprocess.Popen(cmd)
        return process
    
    # Start the process in a thread
    process = run_in_thread()
    
    # Wait a bit and then terminate
    time.sleep(1)
    process.terminate()
    
    # Wait for process to finish
    process.wait()
    
    # Check that no partial torrent file was left behind
    assert not output.exists()

@pytest.mark.parametrize("num_dirs", [10, 50, 100])
def test_batch_scaling(num_dirs: int, tmp_path: Path) -> None:
    """Test how batch processing scales with number of directories."""
    # Create test directories
    parent_dir = tmp_path / "batch_test"
    parent_dir.mkdir()
    output_dir = tmp_path / "torrents"
    
    for i in range(num_dirs):
        subdir = parent_dir / f"dir_{i}"
        subdir.mkdir()
        (subdir / "file.txt").write_text(f"content {i}")
    
    start_time = time.time()
    cmd = [
        "torrent-directories",
        "-v",
        "batch",
        str(parent_dir),
        "http://tracker.example.com:6969/announce",
        "-o",
        str(output_dir)
    ]
    stdout, stderr, code = run_command(cmd)
    end_time = time.time()
    
    processing_time = end_time - start_time
    print(f"\nProcessed {num_dirs} directories in {processing_time:.2f} seconds")
    print(f"Average time per directory: {processing_time/num_dirs:.2f} seconds")
    
    assert code == 0
    assert output_dir.exists()
    torrent_files = list(output_dir.glob("*.torrent"))
    assert len(torrent_files) == num_dirs
    # Based on previous results, set tighter performance requirements
    if num_dirs == 10:
        assert processing_time < 5  # Should process 10 dirs in under 5 seconds
    elif num_dirs == 50:
        assert processing_time < 15  # Should process 50 dirs in under 15 seconds
    else:  # num_dirs == 100
        assert processing_time < 25  # Should process 100 dirs in under 25 seconds 