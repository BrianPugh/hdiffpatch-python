# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

hdiffpatch-python is a high-performance Python wrapper around the [HDiffPatch](https://github.com/sisong/HDiffPatch) C++ library providing efficient binary diff/patch operations with comprehensive compression support. The project uses Cython for C++ integration and supports Python 3.9+.

This project is in **pre-production** and prioritizes **API quality over backward compatibility**. Breaking changes are acceptable for cleaner, more intuitive APIs.

## Development Commands

### Setup and Installation

```bash
# Install development dependencies  
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Build Cython extension (required after editing .pyx files)
poetry install
```

### Testing
This project uses the `pytest` framework for unit testing:

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_compression.py

# Run specific test function
poetry run pytest tests/test_compression.py::TestCompressionTypes::test_compression_type_constants

# Run tests with coverage
poetry run pytest --cov=hdiffpatch --cov-report=html

# Run tests for specific compression type
poetry run pytest -k "compression"
```

### Code Quality

```bash
# Run all pre-commit hooks; this only runs on files tracked by git.
poetry run pre-commit run --all-files
```

## Architecture

**hdiffpatch/_c_extension.pyx**: Main Cython interface wrapping HDiffPatch C++ library

**build.py**: Complex build system with embedded C++ dependencies and aggressive optimizations

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

- **Always** run `poetry install` after editing `.pyx` files to recompile the Cython extension
- Uses Literal types instead of Enums for simplicity and type checker compatibility
- All compression types support both diff creation and patch application
- Use parametrized testing for systematic coverage across compression types

## Development Memories

- Always run `poetry install` after changing Cython code
- Always use `poetry run python` instead of just `python` for running python code
- Always prefer `pathlib.Path` over `os.path`
- Only add comments if the action isn't immediately obvious from function or method names
- **All docstrings must follow numpy-style format** with proper Parameters, Returns, and Raises sections
- TAMP compression is supported as a first-class compression type alongside zlib, zstd, etc.
- All compression types should be tested with round-trip validation
- Use the comprehensive fixture system in `conftest.py` for consistent test data
- Run `pre-commit run --all` before asking to commit to ensure pre-commit passes all checks
- When writing unit tests, prefer to use pytest functionality (such as `parametrize`)
