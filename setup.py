#!/usr/bin/env python3
"""Setup script for hdiffpatch package - uses pre-compiled C++ files."""

import os
import platform
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class CustomBuildExt(build_ext):
    """Custom build_ext to handle C++ standard flags for mixed C/C++ extensions."""

    def build_extension(self, ext):
        # Override the _compile method to add C++ standard only for C++ files
        original_compile = self.compiler._compile

        def custom_compile(obj, src, ext_name, cc_args, extra_postargs, pp_opts):
            # Add C++ standard only for C++ files (not C files)
            if src.endswith((".cpp", ".cxx", ".cc", ".C")):  # noqa: SIM102
                if platform.system() != "Windows":
                    # Add C++11 for Unix-like systems
                    extra_postargs = extra_postargs + ["-std=c++11"]
                # Windows already has /std:c++17 set globally
            return original_compile(obj, src, ext_name, cc_args, extra_postargs, pp_opts)

        self.compiler._compile = custom_compile
        try:
            super().build_extension(ext)
        finally:
            self.compiler._compile = original_compile


def get_sources():
    """Get all C/C++ source files for the extension."""
    base_path = Path("hdiffpatch/_c_src/HDiffPatch")
    lib_path = base_path / "libHDiffPatch"
    md5_path = base_path / ".." / "libmd5"
    lzma_path = base_path / ".." / "lzma" / "C"
    zstd_path = base_path / ".." / "zstd" / "lib"
    bz2_path = base_path / ".." / "bzip2"
    zlib_path = base_path / ".." / "zlib"
    ldef_path = base_path / ".." / "libdeflate"
    tamp_path = base_path / ".." / "tamp" / "tamp" / "_c_src"

    sources = []

    # Core HDiffPatch sources
    sources.extend((lib_path / "HDiff").rglob("*.c"))
    sources.extend((lib_path / "HDiff").rglob("*.cpp"))
    sources.extend((lib_path / "HPatch").rglob("*.c"))
    sources.extend((lib_path / "HPatch").rglob("*.cpp"))
    sources.extend((lib_path / "HPatchLite").rglob("*.c"))
    sources.extend((base_path / "libParallel").rglob("*.cpp"))

    # Compression plugin
    sources.append("hdiffpatch/_c_src/tamp_compress_plugin.cpp")

    # TAMP
    sources.extend(
        [
            tamp_path / "tamp" / "common.c",
            tamp_path / "tamp" / "compressor.c",
            tamp_path / "tamp" / "decompressor.c",
        ]
    )

    # MD5
    sources.append(md5_path / "md5.c")

    # LZMA
    lzma_sources = [
        "7zCrc.c",
        "7zCrcOpt.c",
        "7zStream.c",
        "Alloc.c",
        "Bra.c",
        "Bra86.c",
        "BraIA64.c",
        "CpuArch.c",
        "Delta.c",
        "LzFind.c",
        "LzFindOpt.c",
        "LzFindMt.c",
        "Lzma2Dec.c",
        "Lzma2Enc.c",
        "LzmaDec.c",
        "LzmaEnc.c",
        "MtDec.c",
        "MtCoder.c",
        "Sha256.c",
        "Sha256Opt.c",
        "Threads.c",
        "Xz.c",
        "XzCrc64.c",
        "XzCrc64Opt.c",
        "XzDec.c",
        "XzEnc.c",
    ]
    sources.extend([lzma_path / s for s in lzma_sources])

    # ZSTD
    sources.extend((zstd_path / "common").glob("*.c"))
    sources.extend((zstd_path / "decompress").glob("*.c"))
    sources.extend((zstd_path / "compress").glob("*.c"))

    # BZ2
    bz2_sources = ["blocksort.c", "bzlib.c", "compress.c", "crctable.c", "decompress.c", "huffman.c", "randtable.c"]
    sources.extend([bz2_path / s for s in bz2_sources])

    # ZLIB
    zlib_sources = ["adler32.c", "crc32.c", "inffast.c", "inflate.c", "inftrees.c", "trees.c", "zutil.c", "deflate.c"]
    sources.extend([zlib_path / s for s in zlib_sources])

    # LIBDEFLATE
    sources.extend(
        [
            ldef_path / "lib" / "deflate_decompress.c",
            ldef_path / "lib" / "utils.c",
            ldef_path / "lib" / "x86" / "cpu_features.c",
        ]
    )

    return [str(s) for s in sources]


def get_include_dirs():
    """Get include directories."""
    base_path = Path("hdiffpatch/_c_src/HDiffPatch")
    md5_path = base_path / ".." / "libmd5"
    lzma_path = base_path / ".." / "lzma" / "C"
    zstd_path = base_path / ".." / "zstd" / "lib"
    bz2_path = base_path / ".." / "bzip2"
    zlib_path = base_path / ".." / "zlib"
    ldef_path = base_path / ".." / "libdeflate"
    tamp_path = base_path / ".." / "tamp" / "tamp" / "_c_src"

    return [
        "hdiffpatch",
        "hdiffpatch/_c_src",
        str(base_path),
        str(base_path / "libHDiffPatch"),
        str(base_path / "libHDiffPatch" / "HDiff"),
        str(base_path / "libHDiffPatch" / "HPatch"),
        str(tamp_path),
        str(md5_path),
        str(lzma_path),
        str(zstd_path),
        str(zstd_path / "common"),
        str(zstd_path / "compress"),
        str(zstd_path / "decompress"),
        str(bz2_path),
        str(zlib_path),
        str(ldef_path),
    ]


def get_compile_args():
    """Get platform-specific compile arguments."""
    enable_aggressive_opts = os.environ.get("HDIFFPATCH_AGGRESSIVE_OPTS", "1") == "1"

    # Common defines for all platforms
    common_defines = [
        "-DIS_NOTICE_compress_canceled=0",  # Suppress hdiffpatch compression info messages
        "-D__STDC_LIMIT_MACROS",  # Enable C99 limit macros in C++
        "-D__STDC_CONSTANT_MACROS",  # Enable C99 constant macros in C++
        "-D_ChecksumPlugin_md5",
        "-D_CompressPlugin_lzma",
        "-D_CompressPlugin_lzma2",
        "-D_CompressPlugin_zstd",
        "-DZSTD_HAVE_WEAK_SYMBOLS=0",
        "-DZSTD_TRACE=0",
        "-DZSTD_DISABLE_ASM=1",
        "-DZSTDLIB_VISIBLE=",
        "-DZSTDLIB_HIDDEN=",
        "-D_CompressPlugin_bz2",
        "-D_CompressPlugin_zlib",
        "-D_CompressPlugin_ldef",
        "-D_CompressPlugin_ldef_is_use_zlib",
    ]

    extra_compile_args = common_defines[:]

    if platform.system() == "Windows":
        extra_compile_args.extend(
            [
                "/O2",  # Maximum optimization for Windows
                "/std:c++17",  # Use C++17 standard
                "/D_CRT_SECURE_NO_WARNINGS",
                "/DWIN32_LEAN_AND_MEAN",
                "/favor:blend",  # Optimize for mixed workloads
                "/GL",  # Whole program optimization
                "/wd4996",  # Disable deprecated function warnings
                "/wd4267",  # Disable size_t conversion warnings
                "/wd4244",  # Disable conversion warnings
                "/wd4101",  # Disable unreferenced local variable warnings
            ]
        )
    else:
        extra_compile_args.extend(
            [
                "-O3",  # Maximum optimization for GCC/Clang
                "-fPIC",
                "-Wno-sign-compare",
                "-Wno-unused-function",
                "-Wno-unused-variable",
                "-Wno-unreachable-code",
                "-Wno-unused-but-set-variable",
                # Note: -std=c++11 is added per-file in CustomBuildExt for C++ files only
            ]
        )

        # Add performance optimizations if enabled
        if enable_aggressive_opts:
            extra_compile_args.extend(
                [
                    "-funroll-loops",  # Unroll loops for better performance
                    "-ffast-math",  # Enable fast math optimizations
                ]
            )

            # Platform-specific optimizations
            machine = platform.machine().lower()
            if machine in ["x86_64", "amd64"]:
                extra_compile_args.extend(["-msse4.2", "-mpopcnt"])

        # Enable threading support
        extra_compile_args.append("-pthread")

    return extra_compile_args


def get_link_args():
    """Get platform-specific linker arguments."""
    enable_aggressive_opts = os.environ.get("HDIFFPATCH_AGGRESSIVE_OPTS", "1") == "1"

    extra_link_args = []
    if platform.system() == "Windows":
        if enable_aggressive_opts:
            extra_link_args.extend(["/LTCG"])  # Link-time code generation
    else:
        extra_link_args.extend(["-O3"])  # Basic optimization without LTO

    return extra_link_args


# Define the extension using the pre-compiled C++ file
ext_modules = [
    Extension(
        "hdiffpatch._c_extension",
        sources=["hdiffpatch/_c_extension.cpp"] + get_sources(),
        include_dirs=get_include_dirs(),
        extra_compile_args=get_compile_args(),
        extra_link_args=get_link_args(),
        define_macros=[
            ("_GNU_SOURCE", "1"),
            ("_DARWIN_C_SOURCE", "1"),
            ("_POSIX_C_SOURCE", "200809L"),
            ("_DEFAULT_SOURCE", "1"),  # Enable additional glibc features
        ],
        language="c++",
    ),
]

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": CustomBuildExt},
)
