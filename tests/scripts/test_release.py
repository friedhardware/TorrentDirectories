from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.release import (
    bump_version,
    get_current_version,
    update_pyproject_version,
    update_version,
)


@pytest.fixture
def mock_repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a mock repository root with necessary files."""
    # Create the directory structure
    src_dir = tmp_path / "src" / "torrent"
    src_dir.mkdir(parents=True)

    # Create version.py
    version_content = dedent(
        '''
        """Version information for the torrent package."""
        from __future__ import annotations

        __version__ = "0.7.0"
    '''
    ).lstrip()
    version_file = src_dir / "version.py"
    version_file.write_text(version_content)

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


def test_update_version_in_version_file(mock_repo_root: Path) -> None:
    """Test updating version in version.py."""
    # Update version
    update_version("0.8.0")

    # Check content
    version_file = mock_repo_root / "src" / "torrent" / "version.py"
    content = version_file.read_text()
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
    """Test getting current version from version.py."""
    version = get_current_version()
    assert version == "0.7.0"


def test_get_current_version_missing_file(mock_repo_root: Path) -> None:
    """Test getting version from non-existent file."""
    # Remove the version.py file
    version_file = mock_repo_root / "src" / "torrent" / "version.py"
    version_file.unlink()

    with pytest.raises(FileNotFoundError):
        get_current_version()


def test_get_current_version_invalid_content(mock_repo_root: Path) -> None:
    """Test getting version from file with invalid content."""
    # Replace version.py with invalid content
    version_file = mock_repo_root / "src" / "torrent" / "version.py"
    version_file.write_text('"""Invalid content."""')

    with pytest.raises(RuntimeError, match="Unable to find version string"):
        get_current_version()
