# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

hdiffpatch-python is a high-performance Python wrapper around the [HDiffPatch](https://github.com/sisong/HDiffPatch) C++ library providing efficient binary diff/patch operations with comprehensive compression support. The project uses Cython for C++ integration and supports Python 3.10+. It is a library only — there is no CLI.

## Development Commands

### Setup and Installation

```bash
# Install development dependencies
uv sync

# Build Cython extensions (required after initial sync)
uv run python rebuild.py

# Install pre-commit hooks
uv run pre-commit install
```

### Testing
This project uses the `pytest` framework for unit testing:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_compression.py

# Run specific test function
uv run pytest tests/test_compression.py::TestCompressionTypes::test_compression_type_constants

# Run tests with coverage
uv run pytest --cov=hdiffpatch --cov-report=html

# Run tests matching a keyword
uv run pytest -k "compression"
```

### Code Quality

```bash
# Run all pre-commit hooks; this only runs on files tracked by git.
uv run pre-commit run --all-files
```

Linting/typing is configured in `pyproject.toml`: ruff (line length 120, numpy docstring convention, target Python 3.10) and pyright (checks `tests/`).

## Architecture

### Build pipeline

- **`cythonize.py`**: compiles `hdiffpatch/_c_extension.pyx` to C++ with optimization directives.
- **`rebuild.py`**: runs `cythonize.py`, then reinstalls the package in editable mode. This is the one command to run after editing `.pyx` files.
- **`setup.py`**: builds a single extension module (`hdiffpatch._c_extension`) that statically embeds all C/C++ dependencies from `hdiffpatch/_c_src/` (HDiffPatch, zlib, libdeflate, lzma, zstd, bzip2, tamp, lz4, tinyuz, brotli, lzham, libmd5) with `-O3` and platform-specific optimizations. Compression plugins are enabled via preprocessor defines (e.g. `_CompressPlugin_lzma`).

### Package layout

- **`hdiffpatch/_c_extension.pyx`**: the entire Cython interface — core functions, constants, and the `HDiffPatchError` exception. `hdiffpatch/_c_extension.pyi` is the hand-maintained type stub; keep it in sync when changing the `.pyx` API.
- **`hdiffpatch/_base_config.py`** + per-algorithm config modules (`_zlib_config.py`, `_lzma_config.py`, `_zstd_config.py`, `_bzip2_config.py`, `_tamp_config.py`, `_xz_config.py`, `_lz4_config.py`, `_tuz_config.py`, `_brotli_config.py`, `_lzham_config.py`): frozen attrs classes for fine-grained compression settings. `BaseConfig` defines classmethod presets (`fast`, `balanced`, `best_compression`, `minimal_memory`) that subclasses implement.
- **`hdiffpatch/__init__.py`**: assembles the public API; `__version__` is managed by setuptools-scm — don't edit it.

### Public API

```python
diff(old_data: bytes, new_data: bytes, compression=None, *, validate=True, big_cache_match=False) -> bytes
apply(old_data: bytes, diff_data: bytes) -> bytes      # auto-detects compression from diff header
recompress(diff_data: bytes, compression=None) -> bytes  # re-encode an existing diff (incl. hdiffz output)
```

- `compression` accepts a `CompressionType` literal string (`"none"`, `"zlib"`, `"lzma"`, `"lzma2"`, `"zstd"`, `"bzip2"`, `"tamp"`, `"xz"`, `"lz4"`, `"lz4hc"`, `"tuz"`, `"brotli"`, `"lzham"`), a config object (e.g. `ZStdConfig(level=22)`), or `None`.
- There is a single exception type, `HDiffPatchError`, raised for all diff/patch/compression failures.
- Uses Literal types instead of Enums for simplicity and type checker compatibility.

### Tests

- `tests/conftest.py` provides a comprehensive fixture system (e.g. `simple_text_data`, `binary_data`, `random_data`, `compression_types`, `all_compression_types`) — use these for consistent test data.
- `tests/binaries/` holds real MicroPython firmware images and hdiffz-produced diffs used by `test_binary_compatibility.py` to verify compatibility with upstream HDiffPatch tooling.
- `tools/micropython-binary-demo.py` is a demo script exercising the same firmware-diff use case.

### Adding a codec

A new codec touches every codec list, and missing one fails quietly (a test fixture skips it, or the lite API rejects it):

- `setup.py`: sources, include dirs, and the `-D_CompressPlugin_*` define. Vendor the library as a submodule under `hdiffpatch/_c_src/`; the sdist picks submodules up through setuptools-scm.
- `_c_extension.pyx`: the extern plugin declarations, the `TCompressPlugin_*` struct, `CompressionType`, `COMPRESSION_*`, `_valid_compression_types`, `get_compress_plugin`/`get_decompress_plugin` (which must also accept the diff header's upstream name, e.g. `"7zXZ"`), a `create_custom_*_plugin`, and `_resolve_compression_to_plugin`. If upstream's `hpi_compressType` has a byte for it, also add it to `LiteCompressionType` (the runtime lite set is derived from it), `_lite_compress_type_tag`, `_lite_header_decompress_plugin` and `_lite_normalize_compression`.
- The `.pyi` stub, `__init__.py` exports, a `_<codec>_config.py` module, the `compression_types`/`all_compression_types` fixtures, the sorted "Valid options" message in `tests/test_exceptions.py`, and the lite lists in `tests/test_diff_lite.py`/`tests/test_recompress_lite.py`.

Gotchas:

- Encoders with `threads > 1` (lzma2, xz, tinyuz, lzham) call the output stream's `write()` from worker threads, and upstream plugins default to 4 threads. Stream callbacks must never touch Python objects; write through upstream's C++ `TVectorAsStreamOutput` like `diff`/`recompress` do.
- Multithreaded LZHAM output varies between runs (upstream's plugin can't set `LZHAM_COMP_FLAG_DETERMINISTIC_PARSING`), so byte-identity tests use `LzhamConfig()` (1 thread), never the `"lzham"` string.
- lzham_codec is abandoned upstream; the submodule tracks the `portability` branch of BrianPugh/lzham_codec, so portability fixes go there.
- Test Linux aarch64/GCC locally with Docker: copy the repo into a `python:3.13` container, `pip install --no-build-isolation .` (with `SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0`), then run pytest. Windows/MSVC is CI-only.

## Development Memories

- Always run `uv run python rebuild.py` after `uv sync` for development setup
- After changing Cython code: just run `uv run python rebuild.py` (handles cythonize automatically)
- Always use `uv run python` instead of just `python` for running python code
- Always prefer `pathlib.Path` over `os.path`
- Only add comments if the action isn't immediately obvious from function or method names
- **All docstrings must follow numpy-style format** with proper Parameters, Returns, and Raises sections
- TAMP compression is supported as a first-class compression type alongside zlib, zstd, etc.
- All compression types should be tested with round-trip validation
- Use the comprehensive fixture system in `conftest.py` for consistent test data
- Run `uv run pre-commit run --all-files` before asking to commit to ensure pre-commit passes all checks. It skips untracked files, so `git add` new files first.
- `uv run python` rebuilds the package before running anything, so a helper script can't run while the tree doesn't build (e.g. mid-rebase with conflict markers); use `uv run --no-project python` for those.
- When writing unit tests, prefer to use pytest functionality (such as `parametrize`)
