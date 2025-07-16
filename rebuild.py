#!/usr/bin/env python3
"""Rebuild Cython extensions for development."""

import subprocess
import sys
from pathlib import Path


def rebuild_extensions():
    """Force rebuild of Cython extensions."""
    print("Regenerating C++ from Cython...")

    # First, regenerate C++ files from Cython
    cythonize_result = subprocess.run(  # noqa: S603
        [sys.executable, "cythonize.py"],
        cwd=Path(__file__).parent,
    )

    if cythonize_result.returncode != 0:
        print("❌ Failed to regenerate C++ files")
        sys.exit(1)

    print("Rebuilding Cython extensions...")

    # Use pip to force rebuild the package
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pip", "install", "-e", ".", "--force-reinstall", "--no-deps"], cwd=Path(__file__).parent
    )

    if result.returncode == 0:
        print("✅ Extensions rebuilt successfully!")
        # Test the import
        try:
            import hdiffpatch

            print("✅ Import test passed!")
        except ImportError as e:
            print(f"❌ Import test failed: {e}")
            sys.exit(1)
    else:
        print("❌ Failed to rebuild extensions")
        sys.exit(1)


if __name__ == "__main__":
    rebuild_extensions()
