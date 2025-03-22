"""Tests for CLI option combinations and error code handling."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner

from torrent.cli.main import cli
from torrent.errors.exceptions import ErrorCode


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def test_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a test directory with sample files."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Create test files
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2")

    # Create empty file
    (test_dir / "empty.txt").touch()

    # Create system file
    (test_dir / ".DS_Store").write_text("system file")

    yield test_dir


class TestCLIOptionCombinations:
    """Test various combinations of CLI options."""

    def test_verbose_with_log_file(self, tmp_path: Path) -> None:
        """Test combining verbose output with log file."""
        runner = CliRunner()
        log_file = tmp_path / "test.log"
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "-v",
                    f"--log-file={log_file}",
                    "file",
                    "test.txt",
                    "http://tracker.example.com/announce",
                ],
            )
            assert result.exit_code == 2  # Should fail because file doesn't exist
            assert log_file.exists()

    def test_dry_run_with_force(self, tmp_path: Path) -> None:
        """Test combining dry run with force option."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "--dry-run",
                    "--force",
                    "file",
                    "test.txt",
                    "http://tracker.example.com/announce",
                ],
            )
            assert result.exit_code == 2  # Should fail because file doesn't exist

    def test_multiple_verbosity_levels(self, tmp_path: Path) -> None:
        """Test different verbosity levels."""
        runner = CliRunner()
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        test_file = test_dir / "verbosity_test.txt"
        test_file.write_text("test data")

        # Test verbosity level 3 (most verbose)
        result = runner.invoke(
            cli,
            [
                "-vvv",
                "file",
                str(test_file),
                "http://tracker.example.com/announce",
                "-o",
                str(test_dir / "verbosity_3.torrent"),
            ],
        )
        assert result.exit_code == 0

        # Check for expected log patterns
        pattern = "torrent.core.commands"  # Updated to look for core.commands instead of cli.commands
        assert re.search(
            pattern, result.output
        ), f"Expected pattern '{pattern}' not found in output for verbosity level 3:\n{result.output}"


class TestErrorCodeHandling:
    """Test suite for error code handling."""

    def test_file_exists_error(self, runner: CliRunner, test_dir: Path) -> None:
        """Test error code when output file exists."""
        output_file = test_dir / "exists.torrent"
        output_file.write_text("existing")

        result = runner.invoke(
            cli,
            [
                "file",
                str(test_dir),
                "http://tracker.example.com/announce",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == ErrorCode.FILE_EXISTS.value
        assert "already exists" in result.output.lower()

    def test_invalid_tracker_url(self, runner: CliRunner, test_dir: Path) -> None:
        """Test error code with invalid tracker URL."""
        result = runner.invoke(
            cli,
            [
                "file",
                str(test_dir),
                "invalid-url",
            ],
        )
        assert result.exit_code == ErrorCode.INVALID_TRACKER_URL.value
        assert "invalid tracker url" in result.output.lower()

    def test_empty_directory_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test error code with empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(
            cli,
            [
                "file",
                str(empty_dir),
                "http://tracker.example.com/announce",
            ],
        )
        assert result.exit_code == ErrorCode.NO_DATA.value
        assert "contains no data" in result.output.lower()

    def test_include_system_files_option(
        self, runner: CliRunner, test_dir: Path
    ) -> None:
        """Test that system files are handled correctly with --include-system option."""
        # Create a regular file and a system file
        test_file = test_dir / "content.txt"
        test_file.write_text("regular content")
        system_file = test_dir / ".DS_Store"
        system_file.write_text("system file")

        print("\nTest directory contents:")
        for f in test_dir.iterdir():
            print(f"  {f.name} (exists: {f.exists()})")

        # Test 1: Try to create torrent directly from system file (should fail)
        result = runner.invoke(
            cli,
            [
                "-vvv",
                "file",
                str(system_file),
                "http://tracker.example.com/announce",
                "--include-system",
            ],
        )
        assert result.exit_code == ErrorCode.USAGE_ERROR.value
        assert (
            "system file" in result.output.lower()
            or "not allowed" in result.output.lower()
        )

        # Test 2: Create torrent from directory with system files included (dry run)
        result = runner.invoke(
            cli,
            [
                "-vvv",
                "--dry-run",
                "file",
                str(test_dir),
                "http://tracker.example.com/announce",
                "--include-system",
            ],
        )
        print("\nTest 2 output:")
        print(f"Exit code: {result.exit_code}")
        print(f"Output:\n{result.output}")

        # Check that both regular and system files are listed in dry run output
        assert ".ds_store" in result.output.lower()
        assert "content.txt" in result.output.lower()

        # Test 3: Create actual torrent from directory with system files included
        output_file = test_dir / "output.torrent"
        result = runner.invoke(
            cli,
            [
                "-vvv",
                "file",
                str(test_dir),
                "http://tracker.example.com/announce",
                "--include-system",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_max_failures_option(self, runner: CliRunner, test_dir: Path) -> None:
        """Test max failures option in batch mode."""
        # Create some invalid subdirectories
        (test_dir / "dir1").mkdir()
        (test_dir / "dir2").mkdir()

        result = runner.invoke(
            cli,
            [
                "batch",
                str(test_dir),
                "http://tracker.example.com/announce",
                "--max-failures",
                "1",
            ],
        )
        assert result.exit_code == ErrorCode.MAX_FAILURES_EXCEEDED.value
        assert "maximum failures" in result.output.lower()

    def test_error_code_propagation(self, runner: CliRunner, test_dir: Path) -> None:
        """Test that error codes are properly propagated through the CLI."""
        # Test various error scenarios and verify correct error codes
        scenarios = [
            (
                ["file", "nonexistent", "http://tracker.example.com/announce"],
                ErrorCode.USAGE_ERROR.value,  # Click validates path existence before our code runs
            ),
            (
                ["batch", str(test_dir), "invalid-url"],
                ErrorCode.INVALID_TRACKER_URL.value,
            ),
            (
                ["invalid-command"],
                ErrorCode.USAGE_ERROR.value,
            ),
        ]

        for args, expected_code in scenarios:
            result = runner.invoke(cli, args)
            assert result.exit_code == expected_code
