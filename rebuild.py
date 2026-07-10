#!/usr/bin/env python3
"""Rebuild Cython extensions for development."""

import subprocess
import sys
from pathlib import Path


def rebuild_extensions():
    """Force rebuild of the hdiffpatch package.

    setup.py regenerates C++ from Cython automatically whenever
    _c_extension.pyx is newer than the generated _c_extension.cpp.
    """
    result = subprocess.run(  # noqa: S603
        ["uv", "sync", "--reinstall-package", "hdiffpatch"],  # noqa: S607
        cwd=Path(__file__).parent,
    )
    if result.returncode != 0:
        print("ERROR: Failed to rebuild extensions")
        sys.exit(1)

    try:
        import hdiffpatch  # noqa: F401
    except ImportError as e:
        print(f"ERROR: Import test failed: {e}")
        sys.exit(1)

    print("SUCCESS: Extensions rebuilt.")


if __name__ == "__main__":
    rebuild_extensions()
