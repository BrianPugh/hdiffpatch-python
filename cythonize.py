#!/usr/bin/env python3
"""Pre-compile Cython files to C++ for distribution."""

import os
import platform
from pathlib import Path


def generate_c_extension():
    """Generate C++ file from Cython source."""
    # when using setuptools, you should import setuptools before Cython,
    # otherwise, both might disagree about the class to use.
    from setuptools import Extension  # noqa: I001
    import Cython.Compiler.Options  # pyright: ignore [reportMissingImports]
    from Cython.Build import cythonize  # pyright: ignore [reportMissingImports]

    Cython.Compiler.Options.annotate = True

    base_path = Path("hdiffpatch/_c_src/HDiffPatch")

    include_dirs = [
        "hdiffpatch",
        "hdiffpatch/_c_src",
        str(base_path),
        str(base_path / "libHDiffPatch"),
        str(base_path / "libHDiffPatch" / "HDiff"),
        str(base_path / "libHDiffPatch" / "HPatch"),
    ]

    # Create a minimal extension just for Cython compilation
    extensions = [
        Extension(
            "hdiffpatch._c_extension",
            ["hdiffpatch/_c_extension.pyx"],
            include_dirs=include_dirs,
            language="c++",
        ),
    ]

    # Compile to C++
    cythonize(
        extensions,
        include_path=include_dirs,
        language_level=3,
        annotate=True,
        compiler_directives={
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
            "nonecheck": False,
            "initializedcheck": False,
            "overflowcheck": False,
            "embedsignature": True,
            "optimize.use_switch": True,
            "optimize.unpack_method_calls": True,
        },
    )

    print("SUCCESS: Cython files compiled to C++")
    print("Generated: hdiffpatch/_c_extension.cpp")


if __name__ == "__main__":
    generate_c_extension()
