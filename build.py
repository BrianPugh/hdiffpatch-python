import os
import platform
import shutil
from pathlib import Path

from setuptools import Extension  # noqa: I001
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution  # noqa: I001

# Uncomment if library can still function if extensions fail to compile (e.g. slower, python fallback).
# Don't allow failure if cibuildwheel is running.
# allowed_to_fail = os.environ.get("CIBUILDWHEEL", "0") != "1"
allowed_to_fail = False

base_path = Path("hdiffpatch/_c_src/HDiffPatch")

lib_path = base_path / "libHDiffPatch"

md5_path = base_path / ".." / "libmd5"
lzma_path = base_path / ".." / "lzma" / "C"
zstd_path = base_path / ".." / "zstd" / "lib"
bz2_path = base_path / ".." / "bzip2"
zlib_path = base_path / ".." / "zlib"
ldef_path = base_path / ".." / "libdeflate"
tamp_path = base_path / ".." / "tamp" / "tamp" / "_c_src"


class CustomBuildExt(build_ext):
    """Custom build_ext to handle C++ standard flags for mixed C/C++ extensions."""

    def build_extension(self, ext):
        # Override the _compile method to add C++ standard only for C++ files
        original_compile = self.compiler._compile

        def custom_compile(obj, src, ext_name, cc_args, extra_postargs, pp_opts):
            # Add C++ standard only for C++ files (not C files)
            if src.endswith((".cpp", ".cxx", ".cc", ".C", ".pyx")):  # noqa: SIM102
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


def build_cython_extensions():
    # when using setuptools, you should import setuptools before Cython,
    # otherwise, both might disagree about the class to use.
    import Cython.Compiler.Options  # pyright: ignore [reportMissingImports]
    from Cython.Build import cythonize  # pyright: ignore [reportMissingImports]

    Cython.Compiler.Options.annotate = True

    enable_aggressive_opts = os.environ.get("HDIFFPATCH_AGGRESSIVE_OPTS", "1") == "1"

    # Common defines for all platforms
    common_defines = [
        "-DIS_NOTICE_compress_canceled=0",  # Suppress hdiffpatch compression info messages
        "-D__STDC_LIMIT_MACROS",  # Enable C99 limit macros in C++
        "-D__STDC_CONSTANT_MACROS",  # Enable C99 constant macros in C++
    ]

    extra_compile_args = common_defines[:]
    sources = []
    include_dirs = [
        "hdiffpatch",
        "hdiffpatch/_c_src",
        base_path,
        base_path / "libHDiffPatch",
        base_path / "libHDiffPatch" / "HDiff",
        base_path / "libHDiffPatch" / "HPatch",
    ]

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
                # For x86_64, use specific instruction sets
                extra_compile_args.extend(["-msse4.2", "-mpopcnt"])  # Conservative SIMD instructions
            # Note: Avoid ARM-specific flags for broader compatibility

        # Enable threading support
        extra_compile_args.append("-pthread")

    sources.extend((lib_path / "HDiff").rglob("*.c"))
    sources.extend((lib_path / "HDiff").rglob("*.cpp"))
    sources.extend((lib_path / "HPatch").rglob("*.c"))
    sources.extend((lib_path / "HPatch").rglob("*.cpp"))
    sources.extend((lib_path / "HPatchLite").rglob("*.c"))
    sources.extend((base_path / "libParallel").rglob("*.cpp"))

    # Add raw compression plugin
    sources.append("hdiffpatch/_c_src/tamp_compress_plugin.cpp")

    ########
    # tamp #
    ########
    extra_compile_args.extend(
        [
            "-I" + str(tamp_path),
        ]
    )
    sources.extend(
        [
            tamp_path / "tamp" / "common.c",
            tamp_path / "tamp" / "compressor.c",
            tamp_path / "tamp" / "decompressor.c",
        ]
    )

    #######
    # md5 #
    #######
    extra_compile_args.extend(
        [
            "-D_ChecksumPlugin_md5",
            "-I" + str(md5_path),
        ]
    )
    sources.extend(
        [
            md5_path / "md5.c",
        ]
    )

    ########
    # LZMA #
    ########
    extra_compile_args.extend(
        [
            "-D_CompressPlugin_lzma",
            "-D_CompressPlugin_lzma2",
            "-I" + str(lzma_path),
        ]
    )
    sources.extend(
        [
            lzma_path / "7zCrc.c",
            lzma_path / "7zCrcOpt.c",
            lzma_path / "7zStream.c",
            lzma_path / "Alloc.c",
            lzma_path / "Bra.c",
            lzma_path / "Bra86.c",
            lzma_path / "BraIA64.c",
            lzma_path / "CpuArch.c",
            lzma_path / "Delta.c",
            lzma_path / "LzFind.c",
            lzma_path / "LzFindOpt.c",
            lzma_path / "LzFindMt.c",
            lzma_path / "Lzma2Dec.c",
            lzma_path / "Lzma2Enc.c",
            lzma_path / "LzmaDec.c",
            lzma_path / "LzmaEnc.c",
            lzma_path / "MtDec.c",
            lzma_path / "MtCoder.c",
            lzma_path / "Sha256.c",
            lzma_path / "Sha256Opt.c",
            lzma_path / "Threads.c",
            lzma_path / "Xz.c",
            lzma_path / "XzCrc64.c",
            lzma_path / "XzCrc64Opt.c",
            lzma_path / "XzDec.c",
            lzma_path / "XzEnc.c",
        ]
    )

    ########
    # zstd #
    ########
    extra_compile_args.extend(
        [
            "-D_CompressPlugin_zstd",
            "-DZSTD_HAVE_WEAK_SYMBOLS=0",
            "-DZSTD_TRACE=0",
            "-DZSTD_DISABLE_ASM=1",
            "-DZSTDLIB_VISIBLE=",
            "-DZSTDLIB_HIDDEN=",
            "-I" + str(zstd_path),
            "-I" + str(zstd_path / "common"),
            "-I" + str(zstd_path / "compress"),
            "-I" + str(zstd_path / "decompress"),
        ]
    )
    sources.extend((zstd_path / "common").glob("*.c"))
    sources.extend((zstd_path / "decompress").glob("*.c"))
    sources.extend((zstd_path / "compress").glob("*.c"))

    #######
    # bz2 #
    #######
    extra_compile_args.extend(
        [
            "-D_CompressPlugin_bz2",
            "-I" + str(bz2_path),
        ]
    )
    sources.extend(
        [
            bz2_path / "blocksort.c",
            bz2_path / "bzlib.c",
            bz2_path / "compress.c",
            bz2_path / "crctable.c",
            bz2_path / "decompress.c",
            bz2_path / "huffman.c",
            bz2_path / "randtable.c",
        ]
    )

    ########
    # zlib #
    ########
    extra_compile_args.extend(
        [
            "-D_CompressPlugin_zlib",
            "-I" + str(zlib_path),
        ]
    )
    sources.extend(
        [
            zlib_path / "adler32.c",
            zlib_path / "crc32.c",
            zlib_path / "inffast.c",
            zlib_path / "inflate.c",
            zlib_path / "inftrees.c",
            zlib_path / "trees.c",
            zlib_path / "zutil.c",
            zlib_path / "deflate.c",
        ]
    )

    ########
    # ldef #
    ########
    extra_compile_args.extend(
        [
            "-D_CompressPlugin_ldef",
            "-D_CompressPlugin_ldef_is_use_zlib",
            "-I" + str(ldef_path),
        ]
    )
    sources.extend(
        [
            ldef_path / "lib" / "deflate_decompress.c",
            ldef_path / "lib" / "utils.c",
            ldef_path / "lib" / "x86" / "cpu_features.c",
        ]
    )

    # Add linker flags for optimization
    extra_link_args = []
    if platform.system() == "Windows":
        if enable_aggressive_opts:
            extra_link_args.extend(["/LTCG"])  # Link-time code generation
    else:
        # Conservative linker optimizations that work with mixed C/C++ code
        extra_link_args.extend(["-O3"])  # Basic optimization without LTO to avoid issues

    ##########################
    # C Extension Definition #
    ##########################
    extensions = [
        Extension(
            # Your .pyx file will be available to cpython at this location.
            "hdiffpatch._c_extension",
            [
                "hdiffpatch/_c_extension.pyx",
                *(str(x) for x in sources),
            ],
            include_dirs=[str(x) for x in include_dirs],
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args,
            define_macros=[
                ("_GNU_SOURCE", "1"),
                ("_DARWIN_C_SOURCE", "1"),
                ("_POSIX_C_SOURCE", "200809L"),
                ("_DEFAULT_SOURCE", "1"),  # Enable additional glibc features
            ],
            language="c++",
        ),
    ]

    include_dirs = set()
    for extension in extensions:
        include_dirs.update(extension.include_dirs)
    include_dirs = list(include_dirs)

    ext_modules = cythonize(
        extensions,
        include_path=include_dirs,
        language_level=3,
        annotate=True,
        compiler_directives={
            "boundscheck": False,  # Disable bounds checking for performance
            "wraparound": False,  # Disable negative index wrapping
            "cdivision": True,  # Use C division semantics
            "nonecheck": False,  # Disable None checks for performance
            "initializedcheck": False,  # Disable initialization checks
            "overflowcheck": False,  # Disable overflow checking
            "embedsignature": True,  # Embed function signatures in docstrings
            "optimize.use_switch": True,  # Use switch statements for optimization
            "optimize.unpack_method_calls": True,  # Unpack method calls
        },
    )
    dist = Distribution({"ext_modules": ext_modules})
    cmd = CustomBuildExt(dist)
    cmd.ensure_finalized()
    cmd.run()

    for output in cmd.get_outputs():
        output = Path(output)
        relative_extension = output.relative_to(cmd.build_lib)
        shutil.copyfile(output, relative_extension)


try:
    build_cython_extensions()
except Exception:
    if not allowed_to_fail:
        raise
