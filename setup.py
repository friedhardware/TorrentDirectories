"""
Setup configuration for TorrentDirectories package.
"""

from __future__ import annotations

import re
from pathlib import Path

from setuptools import find_packages, setup


# Read the version from version.py
def get_version() -> str:
    """Get the version string from version.py.

    Returns:
        str: The version string from version.py.

    Raises:
        RuntimeError: If version string cannot be found.
    """
    version_file = Path(__file__).parent / "src" / "torrent" / "version.py"
    with open(version_file) as f:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
        if version_match:
            return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="torrent-directories",
    version=get_version(),
    description="A tool for creating torrent files from directories",
    author="Josh S",
    author_email="friedhardware@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.13",
    install_requires=[
        "libtorrent>=2.0.0",
        "click>=8.1.3",
    ],
    extras_require={
        "dev": [
            "setuptools>=76.0.0",
            "pytest>=8.0.0",
            "pytest-cov>=6.0.0",
            "pytest-mock>=3.14.0",
            "click>=8.1.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "torrent-directories=torrent.cli.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
    ],
)
