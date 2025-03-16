from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture

from torrent.cli.parser import create_parser


def test_file_command_validates_paths(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    parser = create_parser()

    # Should fail with invalid characters
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["file", "bad/*/path", "http://tracker.example.com"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err

    # Should fail with path traversal
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["file", "../../../etc/passwd", "http://tracker.example.com"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err

    # Should succeed with valid path
    valid_dir = tmp_path / "valid_directory"
    valid_dir.mkdir()
    args = parser.parse_args(["file", str(valid_dir), "http://tracker.example.com"])
    assert args.input_path == str(valid_dir)


def test_batch_command_requires_directory(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    parser = create_parser()

    # Should fail if directory doesn't exist
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(
            ["batch", str(tmp_path / "nonexistent"), "http://tracker.example.com"]
        )
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err

    # Should fail if path is a file
    file_path = tmp_path / "file.txt"
    file_path.touch()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["batch", str(file_path), "http://tracker.example.com"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "is not a directory" in captured.err

    # Should succeed with valid directory
    valid_dir = tmp_path / "valid_directory"
    valid_dir.mkdir()
    args = parser.parse_args(["batch", str(valid_dir), "http://tracker.example.com"])
    assert args.directory == str(valid_dir)
