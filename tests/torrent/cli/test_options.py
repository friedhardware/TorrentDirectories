"""Tests for CLI option functionality."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from torrent.cli.main import cli


@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    """Create a test directory for file operations."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    return test_dir


class TestForceOption:
    """Test cases for the --force option."""

    def test_force_option_file_command(self, runner: CliRunner, test_dir: Path) -> None:
        """Test that --force allows overwriting existing files."""
        test_file = test_dir / "test.txt"
        test_file.write_text("test content")

        # Create existing torrent file
        torrent_file = test_dir / "test.txt.torrent"
        torrent_file.write_text("existing torrent")

        # Try without force
        result = runner.invoke(
            cli,
            ["file", str(test_file), "http://tracker.com"],
            catch_exceptions=False,
        )
        assert result.exit_code == 12  # FILE_EXISTS error code
        assert "Output file already exists" in result.output
        assert "Use --force to overwrite existing files" in result.output

        # Try with force
        result = runner.invoke(
            cli,
            ["--force", "file", str(test_file), "http://tracker.com"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert torrent_file.exists()

    def test_force_option_batch_command(
        self, runner: CliRunner, test_dir: Path
    ) -> None:
        """Test that --force allows overwriting existing files in batch mode."""
        # Create test directory with content
        content_dir = test_dir / "content_dir"
        content_dir.mkdir(exist_ok=True)
        (content_dir / "file.txt").write_text("content")

        # Create output directory with existing torrent
        output_dir = test_dir / "torrents"
        output_dir.mkdir(exist_ok=True)
        (output_dir / "content_dir.torrent").write_text("existing torrent")

        # Try without force
        result = runner.invoke(
            cli,
            [
                "batch",
                str(test_dir),
                "http://tracker.com",
                "--output",
                str(output_dir),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 23  # BATCH_PROCESSING_ERROR
        assert "Output file already exists" in result.output
        assert "Use --force to overwrite existing files" in result.output

        # Try with force
        result = runner.invoke(
            cli,
            [
                "--force",
                "batch",
                str(test_dir),
                "http://tracker.com",
                "--output",
                str(output_dir),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert (output_dir / "content_dir.torrent").exists()


class TestTimestampHandling:
    """Test cases for timestamp handling."""

    def test_force_updates_timestamps_batch(
        self, runner: CliRunner, test_dir: Path
    ) -> None:
        """Test that --force updates timestamps in batch mode."""
        # Create test directories
        for i in range(3):
            dir_path = test_dir / f"dir{i}"
            dir_path.mkdir(exist_ok=True)
            (dir_path / "file.txt").write_text(f"content {i}")

        # Create output directory
        output_dir = test_dir / "torrents"
        output_dir.mkdir(exist_ok=True)

        # Create initial torrents
        result = runner.invoke(
            cli,
            [
                "batch",
                str(test_dir),
                "http://tracker.com",
                "--output",
                str(output_dir),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Get initial timestamps
        initial_timestamps = {}
        for i in range(3):
            torrent_path = output_dir / f"dir{i}.torrent"
            initial_timestamps[torrent_path] = torrent_path.stat().st_mtime

        # Update content and recreate torrents with --force
        for i in range(3):
            (test_dir / f"dir{i}" / "file.txt").write_text(f"updated content {i}")

        result = runner.invoke(
            cli,
            [
                "--force",
                "batch",
                str(test_dir),
                "http://tracker.com",
                "--output",
                str(output_dir),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Verify timestamps were updated
        for i in range(3):
            torrent_path = output_dir / f"dir{i}.torrent"
            assert torrent_path.stat().st_mtime > initial_timestamps[torrent_path]
