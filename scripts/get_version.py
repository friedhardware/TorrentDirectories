#!/usr/bin/env python3
import re
from pathlib import Path

def get_version():
    init_file = Path(__file__).parent.parent / "src" / "torrent" / "__init__.py"
    with open(init_file) as f:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
        if version_match:
            return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

if __name__ == "__main__":
    print(get_version()) 