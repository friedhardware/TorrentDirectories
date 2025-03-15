#!/usr/bin/env python3
import re
import sys
from pathlib import Path
import subprocess

def update_version(new_version):
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

def main():
    if len(sys.argv) != 2:
        print("Usage: ./release.py <new_version>")
        print("Example: ./release.py 0.4.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # Update version in __init__.py
    update_version(new_version)
    
    # Create git tag
    subprocess.run(["git", "tag", f"v{new_version}"])
    
    print(f"Version updated to {new_version}")
    print(f"Created git tag v{new_version}")
    print("\nNext steps:")
    print("1. Review changes: git diff")
    print("2. Commit changes: git commit -am 'Release v{new_version}'")
    print("3. Push changes: git push")
    print("4. Push tag: git push --tags")
    print("5. Build and publish: python -m build && python -m twine upload dist/*")

if __name__ == "__main__":
    main() 