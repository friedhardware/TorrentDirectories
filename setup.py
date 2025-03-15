"""
Setup configuration for TorrentDirectories package.
"""
from setuptools import setup, find_packages

setup(
    name="torrent-directories",
    version="0.1.0",
    description="A tool for creating torrent files from directories",
    author="Josh S",
    author_email="friedhardware@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=[
        "libtorrent>=2.0.0",
        "pywin32>=228; platform_system=='Windows'",
    ],
    entry_points={
        "console_scripts": [
            "torrent-directories=torrent.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
    ],
) 