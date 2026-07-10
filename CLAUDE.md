# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

hdiffpatch-python is a high-performance Python wrapper around the [HDiffPatch](https://github.com/sisong/HDiffPatch) C++ library providing efficient binary diff/patch operations with comprehensive compression support. The project uses Cython for C++ integration and supports Python 3.9+. It is a library only — there is no CLI.

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

Linting/typing is configured in `pyproject.toml`: ruff (line length 120, numpy docstring convention, target Python 3.9) and pyright (checks `tests/`).

## Architecture

### Build pipeline

- **`cythonize.py`**: compiles `hdiffpatch/_c_extension.pyx` to C++ with optimization directives.
- **`rebuild.py`**: runs `cythonize.py`, then reinstalls the package in editable mode. This is the one command to run after editing `.pyx` files.
- **`setup.py`**: builds a single extension module (`hdiffpatch._c_extension`) that statically embeds all C/C++ dependencies from `hdiffpatch/_c_src/` (HDiffPatch, zlib, libdeflate, lzma, zstd, bzip2, tamp, libmd5) with `-O3` and platform-specific optimizations. Compression plugins are enabled via preprocessor defines (e.g. `_CompressPlugin_lzma`).

### Package layout

- **`hdiffpatch/_c_extension.pyx`**: the entire Cython interface — core functions, constants, and the `HDiffPatchError` exception. `hdiffpatch/_c_extension.pyi` is the hand-maintained type stub; keep it in sync when changing the `.pyx` API.
- **`hdiffpatch/_base_config.py`** + per-algorithm config modules (`_zlib_config.py`, `_lzma_config.py`, `_zstd_config.py`, `_bzip2_config.py`, `_tamp_config.py`): frozen attrs classes for fine-grained compression settings. `BaseConfig` defines classmethod presets (`fast`, `balanced`, `best_compression`, `minimal_memory`) that subclasses implement.
- **`hdiffpatch/__init__.py`**: assembles the public API; `__version__` is managed by setuptools-scm — don't edit it.

### Public API

```python
diff(old_data: bytes, new_data: bytes, compression=None, *, validate=True) -> bytes
apply(old_data: bytes, diff_data: bytes) -> bytes      # auto-detects compression from diff header
recompress(diff_data: bytes, compression=None) -> bytes  # re-encode an existing diff (incl. hdiffz output)
```

- `compression` accepts a `CompressionType` literal string (`"none"`, `"zlib"`, `"lzma"`, `"lzma2"`, `"zstd"`, `"bzip2"`, `"tamp"`), a config object (e.g. `ZStdConfig(level=22)`), or `None`.
- There is a single exception type, `HDiffPatchError`, raised for all diff/patch/compression failures.
- Uses Literal types instead of Enums for simplicity and type checker compatibility.

### Tests

- `tests/conftest.py` provides a comprehensive fixture system (e.g. `simple_text_data`, `binary_data`, `random_data`, `compression_types`, `all_compression_types`) — use these for consistent test data.
- `tests/binaries/` holds real MicroPython firmware images and hdiffz-produced diffs used by `test_binary_compatibility.py` to verify compatibility with upstream HDiffPatch tooling.
- `tools/micropython-binary-demo.py` is a demo script exercising the same firmware-diff use case.

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
- Run `uv run pre-commit run --all-files` before asking to commit to ensure pre-commit passes all checks
- When writing unit tests, prefer to use pytest functionality (such as `parametrize`)
