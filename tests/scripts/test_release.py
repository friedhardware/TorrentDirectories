from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock

import pytest

from scripts.release import (
    bump_version,
    get_current_version,
    update_pyproject_version,
    update_version,
)
from torrent.client.web import WebInterface


@pytest.fixture
def mock_repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a mock repository root with necessary files."""
    # Create the directory structure
    src_dir = tmp_path / "src" / "torrent"
    src_dir.mkdir(parents=True)

    # Create __init__.py
    init_content = dedent(
        '''
        """Package initialization."""
        from __future__ import annotations

        __version__ = "0.7.0"
        __all__ = ["TorrentCreator"]
    '''
    ).lstrip()
    init_file = src_dir / "__init__.py"
    init_file.write_text(init_content)

    # Create pyproject.toml
    pyproject_content = dedent(
        """
        [build-system]
        requires = ["setuptools>=61.0"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "torrent-directories"
        version = "0.7.0"
        description = "A tool for creating torrent files from directories"
    """
    ).lstrip()
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject_content)

    # Mock the script path to use our temporary directory
    script_dir = tmp_path / "scripts"
    script_dir.mkdir()
    monkeypatch.setattr("scripts.release.__file__", str(script_dir / "release.py"))

    return tmp_path


def test_bump_version_minor(mock_repo_root: Path) -> None:
    """Test bumping minor version."""
    assert bump_version("0.7.0", "minor") == "0.8.0"
    assert bump_version("1.9.5", "minor") == "1.10.0"


def test_bump_version_major(mock_repo_root: Path) -> None:
    """Test bumping major version."""
    assert bump_version("0.7.0", "major") == "1.0.0"
    assert bump_version("2.3.4", "major") == "3.0.0"


def test_bump_version_patch(mock_repo_root: Path) -> None:
    """Test bumping patch version."""
    assert bump_version("0.7.0", "patch") == "0.7.1"
    assert bump_version("1.2.9", "patch") == "1.2.10"


def test_bump_version_invalid(mock_repo_root: Path) -> None:
    """Test bumping with invalid type."""
    with pytest.raises(ValueError, match="Invalid bump type: invalid"):
        bump_version("0.7.0", "invalid")


def test_update_version_in_init(mock_repo_root: Path) -> None:
    """Test updating version in __init__.py."""
    # Update version
    update_version("0.8.0")

    # Check content
    init_file = mock_repo_root / "src" / "torrent" / "__init__.py"
    content = init_file.read_text()
    assert '__version__ = "0.8.0"' in content
    assert content.count("__version__") == 1


def test_update_version_in_pyproject(mock_repo_root: Path) -> None:
    """Test updating version in pyproject.toml."""
    # Update version
    update_pyproject_version("0.8.0")

    # Check content
    pyproject_file = mock_repo_root / "pyproject.toml"
    content = pyproject_file.read_text()
    assert 'version = "0.8.0"' in content
    assert content.count("version =") == 1


def test_get_current_version(mock_repo_root: Path) -> None:
    """Test getting current version from __init__.py."""
    version = get_current_version()
    assert version == "0.7.0"


def test_get_current_version_missing_file(mock_repo_root: Path) -> None:
    """Test getting version from non-existent file."""
    # Remove the __init__.py file
    init_file = mock_repo_root / "src" / "torrent" / "__init__.py"
    init_file.unlink()

    with pytest.raises(FileNotFoundError):
        get_current_version()


def test_get_current_version_invalid_content(mock_repo_root: Path) -> None:
    """Test getting version from file with invalid content."""
    # Replace __init__.py with invalid content
    init_file = mock_repo_root / "src" / "torrent" / "__init__.py"
    init_file.write_text('"""Invalid content."""')

    with pytest.raises(RuntimeError, match="Unable to find version string"):
        get_current_version()


def test_web_interface_initialization() -> None:
    """Test web interface initialization."""
    web = WebInterface(port=5001)
    assert web.port == 5001
    assert web.torrents == {}
    assert web.errors == []
    assert web.batch_status == {
        "is_running": False,
        "last_run": 0,
        "next_check": 0,
        "message": None,
        "success": False,
        "failure": False,
    }


def test_web_interface_update_torrents() -> None:
    """Test updating torrents in web interface."""
    web = WebInterface()

    # Mock torrent handle
    mock_handle = MagicMock()
    mock_status = MagicMock()
    mock_status.is_seeding = True
    mock_status.is_downloading = False
    mock_status.progress = 1.0
    mock_status.download_rate = 1024  # 1 KB/s
    mock_status.upload_rate = 2048  # 2 KB/s
    mock_handle.status.return_value = mock_status

    # Update torrents
    torrents = {"test.torrent": mock_handle}
    web.update_torrents(torrents)

    assert len(web.torrents) == 1
    assert web.torrents["test.torrent"]["name"] == "test.torrent"
    assert web.torrents["test.torrent"]["status"] == "seeding"
    assert web.torrents["test.torrent"]["progress"] == 100
    assert web.torrents["test.torrent"]["download_rate"] == "1.0 KB/s"
    assert web.torrents["test.torrent"]["upload_rate"] == "2.0 KB/s"


def test_web_interface_update_batch_status() -> None:
    """Test updating batch status in web interface."""
    web = WebInterface()

    # Update batch status
    web.update_batch_status(
        is_running=True,
        last_run=1234567890,
        next_check=1234567890 + 300,
        message="Running batch process",
        success=False,
        failure=False,
    )

    assert web.batch_status["is_running"] is True
    assert web.batch_status["last_run"] == 1234567890
    assert web.batch_status["next_check"] == 1234567890 + 300
    assert web.batch_status["message"] == "Running batch process"
    assert web.batch_status["success"] is False
    assert web.batch_status["failure"] is False


def test_web_interface_add_error() -> None:
    """Test adding errors to web interface."""
    web = WebInterface()

    # Add errors
    web.add_error("Test error 1")
    web.add_error("Test error 2")
    web.add_error("Test error 3")

    assert len(web.errors) == 3
    assert web.errors == ["Test error 1", "Test error 2", "Test error 3"]

    # Test error limit (should keep only last 10)
    for i in range(12):
        web.add_error(f"Error {i}")

    assert len(web.errors) == 10
    assert web.errors[0] == "Error 2"  # First error should be the third error we added
    assert web.errors[-1] == "Error 11"  # Last error should be newest


def test_web_interface_stats() -> None:
    """Test getting statistics from web interface."""
    web = WebInterface()

    # Mock torrent handles
    mock_handle = MagicMock()
    mock_status = MagicMock()
    mock_status.is_seeding = True
    mock_status.is_downloading = False
    mock_handle.status.return_value = mock_status

    # Add torrents
    web.torrents = {
        "torrent1.torrent": {"status": "seeding"},
        "torrent2.torrent": {"status": "seeding"},
        "torrent3.torrent": {"status": "downloading"},
        "torrent4.torrent": {"status": "error"},
    }

    stats = web._get_stats()

    assert stats["total"] == 4
    assert stats["seeding"] == 2
    assert stats["downloading"] == 1
    assert stats["errors"] == 1


def test_web_interface_batch_handlers() -> None:
    """Test batch process handlers in web interface."""
    web = WebInterface()

    # Mock handlers
    start_called = False
    stop_called = False

    def on_start():
        nonlocal start_called
        start_called = True

    def on_stop():
        nonlocal stop_called
        stop_called = True

    # Set handlers
    web.set_batch_handlers(on_start, on_stop)

    # Test handlers
    assert web._on_start == on_start
    assert web._on_stop == on_stop

    # Test handler execution
    web._on_start()
    assert start_called is True

    web._on_stop()
    assert stop_called is True


def test_web_interface_routes() -> None:
    """Test web interface routes."""
    web = WebInterface()

    # Test index route
    with web.app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200

    # Test status route
    with web.app.test_client() as client:
        response = client.get("/status")
        assert response.status_code == 200
        data = response.get_json()
        assert "torrents" in data
        assert "errors" in data
        assert "batch_status" in data
        assert "stats" in data

    # Test batch start route without handler
    with web.app.test_client() as client:
        response = client.post("/batch/start")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    # Test batch stop route without handler
    with web.app.test_client() as client:
        response = client.post("/batch/stop")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    # Test batch routes with handlers
    start_called = False
    stop_called = False

    def on_start():
        nonlocal start_called
        start_called = True

    def on_stop():
        nonlocal stop_called
        stop_called = True

    web.set_batch_handlers(on_start, on_stop)

    with web.app.test_client() as client:
        response = client.post("/batch/start")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert start_called is True

        response = client.post("/batch/stop")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert stop_called is True


def test_web_interface_with_client() -> None:
    """Test web interface integration with TorrentClient."""
    # Implementation needed
    pass


def test_web_interface_dark_mode() -> None:
    """Test dark mode functionality."""
    # Implementation needed
    pass


def test_web_interface_real_time_updates() -> None:
    """Test real-time status updates in web interface."""
    # Implementation needed
    pass
