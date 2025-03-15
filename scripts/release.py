#!/usr/bin/env python3
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse
from typing import Optional, Tuple

def get_current_version() -> str:
    """Get the current version from __init__.py"""
    init_file = Path(__file__).parent.parent / "src" / "torrent" / "__init__.py"
    with open(init_file) as f:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
        if version_match:
            return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

def update_version(new_version: str) -> None:
    """Update version in __init__.py"""
    init_file = Path(__file__).parent.parent / "src" / "torrent" / "__init__.py"
    with open(init_file) as f:
        content = f.read()
    
    new_content = re.sub(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        f'__version__ = "{new_version}"',
        content,
        flags=re.M
    )
    
    with open(init_file, 'w') as f:
        f.write(new_content)

def run_tests() -> bool:
    """Run the test suite"""
    print("\nRunning tests...")
    result = subprocess.run(["python", "-m", "pytest", "-v"], capture_output=True, text=True)
    print(result.stdout)
    return result.returncode == 0

def get_git_changes() -> str:
    """Get git changes since last tag, grouped by type and including authors"""
    # Get the last tag
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        # No tags found, get all commits
        last_tag = None
    else:
        last_tag = result.stdout.strip()

    # Get commits since last tag with author information and commit hash
    if last_tag:
        result = subprocess.run(
            ["git", "log", f"{last_tag}..HEAD", "--pretty=format:%h|%s|%an", "--no-merges"],
            capture_output=True,
            text=True
        )
    else:
        # If no tags exist, get all commits
        result = subprocess.run(
            ["git", "log", "--pretty=format:%h|%s|%an", "--no-merges"],
            capture_output=True,
            text=True
        )
    
    # Get the remote URL to construct GitHub links
    remote_result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True
    )
    remote_url = remote_result.stdout.strip()
    # Convert SSH URL to HTTPS if needed
    if remote_url.startswith('git@github.com:'):
        remote_url = remote_url.replace('git@github.com:', 'https://github.com/')
    # Remove .git suffix if present
    remote_url = remote_url.rstrip('.git')
    
    # Group commits by type
    commits = result.stdout.strip().split('\n')
    grouped_commits = {
        'Features': [],
        'Bug Fixes': [],
        'Documentation': [],
        'Other Changes': []
    }
    
    for commit in commits:
        if not commit.strip():
            continue
        hash_, message, author = commit.split('|', 2)
        commit_url = f"{remote_url}/commit/{hash_}"
        
        # Categorize based on conventional commit prefixes
        if message.startswith('feat:'):
            grouped_commits['Features'].append(f"* {message[6:]} ([{hash_[:7]}])({commit_url}) ({author})")
        elif message.startswith('fix:'):
            grouped_commits['Bug Fixes'].append(f"* {message[5:]} ([{hash_[:7]}])({commit_url}) ({author})")
        elif message.startswith('docs:'):
            grouped_commits['Documentation'].append(f"* {message[6:]} ([{hash_[:7]}])({commit_url}) ({author})")
        else:
            grouped_commits['Other Changes'].append(f"* {message} ([{hash_[:7]}])({commit_url}) ({author})")
    
    # Build the changelog text
    changelog = []
    for category, commits in grouped_commits.items():
        if commits:
            changelog.append(f"\n### {category}")
            changelog.extend(commits)
    
    return '\n'.join(changelog)

def create_changelog(version: str) -> None:
    """Create or update CHANGELOG.md"""
    changelog_file = Path(__file__).parent.parent / "CHANGELOG.md"
    changes = get_git_changes()
    
    if not changelog_file.exists():
        with open(changelog_file, 'w') as f:
            f.write(f"# Changelog\n\n")
    
    with open(changelog_file, 'r') as f:
        content = f.read()
    
    new_entry = f"\n## {version} ({datetime.now().strftime('%Y-%m-%d')})\n\n{changes}"
    
    # Insert new entry after the first heading
    new_content = re.sub(
        r"(# Changelog\n)",
        f"\\1{new_entry}",
        content
    )
    
    with open(changelog_file, 'w') as f:
        f.write(new_content)

def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version according to semantic versioning"""
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

def check_git_status() -> bool:
    """Check if git working directory is clean"""
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    return not result.stdout.strip()

def create_git_tag(version: str) -> None:
    """Create and push git tag"""
    tag = f"v{version}"
    subprocess.run(["git", "tag", tag], check=True)
    subprocess.run(["git", "push", "origin", tag], check=True)

def build_and_publish() -> None:
    """Build and publish the package"""
    print("\nBuilding package...")
    subprocess.run(["python", "-m", "build"], check=True)
    
    print("\nPublishing to PyPI...")
    subprocess.run(["python", "-m", "twine", "upload", "dist/*"], check=True)

def main():
    parser = argparse.ArgumentParser(description='Release a new version of TorrentDirectories')
    parser.add_argument('--bump', choices=['major', 'minor', 'patch'], 
                      help='Type of version bump (default: minor)')
    parser.add_argument('--version', help='Specific version to release')
    parser.add_argument('--no-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--no-publish', action='store_true', help='Skip publishing to PyPI')
    args = parser.parse_args()

    # Check git status
    if not check_git_status():
        print("Error: Git working directory is not clean. Please commit or stash changes.")
        sys.exit(1)

    # Determine new version
    current_version = get_current_version()
    if args.version:
        new_version = args.version
    elif args.bump:
        new_version = bump_version(current_version, args.bump)
    else:
        new_version = bump_version(current_version, 'minor')  # Default to minor bump

    print(f"\nCurrent version: {current_version}")
    print(f"New version: {new_version}")

    # Run tests unless skipped
    if not args.no_tests and not run_tests():
        print("\nError: Tests failed. Aborting release.")
        sys.exit(1)

    # Update version and create changelog
    update_version(new_version)
    create_changelog(new_version)

    # Commit changes
    subprocess.run(["git", "add", "src/torrent/__init__.py", "CHANGELOG.md"], check=True)
    subprocess.run(["git", "commit", "-m", f"Release v{new_version}"], check=True)
    subprocess.run(["git", "push"], check=True)

    # Create and push tag
    create_git_tag(new_version)

    # Build and publish unless skipped
    if not args.no_publish:
        build_and_publish()

    print(f"\nRelease v{new_version} completed successfully!")
    print("\nNext steps:")
    print("1. Review the changes in CHANGELOG.md")
    print("2. Create a GitHub release with the new tag")
    print("3. Update any documentation or website content")

if __name__ == "__main__":
    main() 