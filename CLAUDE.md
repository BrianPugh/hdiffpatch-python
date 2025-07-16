# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

hdiffpatch-python is a high-performance Python wrapper around the [HDiffPatch](https://github.com/sisong/HDiffPatch) C++ library providing efficient binary diff/patch operations with comprehensive compression support. The project uses Cython for C++ integration and supports Python 3.9+.

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

# Run tests for specific compression type
uv run pytest -k "compression"
```

### Code Quality

```bash
# Run all pre-commit hooks; this only runs on files tracked by git.
uv run pre-commit run --all-files
```

## Architecture

**hdiffpatch/_c_extension.pyx**: Main Cython interface wrapping HDiffPatch C++ library

**setup.py**: Complex build system with embedded C++ dependencies and aggressive optimizations

**hdiffpatch/_c_src/**: Embedded C++ dependencies (HDiffPatch, compression libraries, etc.)

### API Design

The API uses pure Literal types for type safety. Supported compression types: `none`, `zlib`, `lzma`, `lzma2`, `zstd`, `bzip2`, `tamp`.

```python
# Core functions
diff(old_data: bytes, new_data: bytes, compression="none") -> bytes
apply(old_data: bytes, diff_data: bytes) -> bytes  # Auto-detects compression

# Exception hierarchy
HDiffPatchError (base exception)
├── DiffError (diff creation failures)
├── PatchError (patch application failures)
└── CompressionError (compression/decompression failures)
```

## Development Notes

- **Run `uv run python rebuild.py`** after `uv sync` to build Cython extensions for development
- **After editing `.pyx` files**, just run `uv run python rebuild.py` (automatically runs cythonize.py first)
- Uses Literal types instead of Enums for simplicity and type checker compatibility
- All compression types support both diff creation and patch application
- Use parametrized testing for systematic coverage across compression types

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
