"""
Setup configuration for TorrentDirectories package.
"""
from setuptools import setup, find_packages
from pathlib import Path
import re

# Read the version from __init__.py
def get_version():
    init_file = Path(__file__).parent / "src" / "torrent" / "__init__.py"
    with open(init_file) as f:
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
    python_requires=">=3.7",
    install_requires=[
        "libtorrent>=2.0.0",
    ],
    extras_require={
        "dev": [
            "setuptools>=76.0.0",
            "pytest>=8.0.0",
            "pytest-cov>=6.0.0",
            "pytest-mock>=3.14.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "torrent-directories=torrent.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 